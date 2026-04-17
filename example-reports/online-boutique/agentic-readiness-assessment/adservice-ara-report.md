# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/adservice
**Date**: 2026-04-16
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Service Archetype**: stateless-utility (user-provided)
**Agent Scope**: read-only
**Priority**: P2
**Tags**: java, grpc, ads
**Context**: Java gRPC service serving contextual ads based on product categories.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISKs**: 12 | **INFOs**: 18

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. The single blocker (AUTH-Q1: no machine identity authentication) must be resolved before any agent can safely call this service. The 12 RISKs are manageable with compensating controls once the blocker is cleared.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 1 |
| RISK | 12 |
| INFO | 18 |
| N/A | 0 |
| Not Evaluated (extended) | 12 |
| **Total** | **43** |

**Core Questions Evaluated**: 24
**Extended Questions Triggered**: 7
**Extended Questions Not Triggered**: 12
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (user-provided)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server is created via `ServerBuilder.forPort(port)` in `AdService.java` (line 56) with no authentication interceptor, no TLS configuration, and no credential verification. The server accepts all incoming connections on the configured port (default 9555). Istio AuthorizationPolicies are disabled (`authorizationPolicies.create: false` in `helm-chart/values.yaml`), so there is no mesh-level caller identity enforcement. Network policies are also disabled (`networkPolicies.create: false`), meaning any pod in the cluster can reach the service. No OAuth2 client credentials flow, no API key authentication, no mTLS configuration at the application layer, and no service account validation in code.
- **Gap**: No machine identity authentication exists at any layer. Any network-reachable client can call `GetAds` without presenting credentials. An agent cannot be identified, attributed, or distinguished from any other caller.
- **Remediation**:
  - **Immediate**: Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true` in `helm-chart/values.yaml`) to enforce mTLS-based caller identity at the mesh layer. This provides machine identity via Istio service account principals without application code changes.
  - **Target State**: Mesh-level mTLS authentication with per-caller AuthorizationPolicy rules. Agent-specific K8s ServiceAccounts with dedicated Istio principals. Application-layer gRPC `ServerInterceptor` for defense-in-depth identity verification.
  - **Estimated Effort**: Low (Helm value change for immediate), Medium (application-layer interceptor)
  - **Dependencies**: AUTH-Q2 (scoped permissions require identity first), AUTH-Q6 (audit logging requires principal attribution)
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 56, `ServerBuilder.forPort(port)` with no auth), `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `networkPolicies.create: false`), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy template exists but is gated by disabled flag)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The service API is defined in `src/main/proto/demo.proto` using Protocol Buffers. The proto file defines the `AdService` with a single `GetAds` RPC, along with `AdRequest`, `AdResponse`, and `Ad` message types. Protobuf is a machine-readable IDL, but the proto file is a monolithic definition containing all 10 services in the Online Boutique — not a standalone spec for the ad service. No OpenAPI, AsyncAPI, or standalone gRPC reflection is configured. The `grpc-services` dependency in `build.gradle` includes health check support but gRPC server reflection is not explicitly enabled in `AdService.java`.
- **Gap**: No standalone machine-readable spec for the ad service. The proto file is shared across all services and not published independently. No gRPC server reflection enabled for runtime discovery.
- **Compensating Controls**:
  - The `demo.proto` file can be used directly to generate gRPC client stubs for agent tool definitions
  - Extract the `AdService` definition into a standalone proto file for agent-specific tool generation
- **Remediation Timeline**: 14–30 days
- **Recommendation**: Enable gRPC server reflection by adding `ProtoReflectionService` to the server builder. Consider extracting `AdService`-specific proto definitions into a standalone file.
- **Evidence**: `src/main/proto/demo.proto` (AdService definition, lines 253–268), `build.gradle` (`io.grpc:grpc-services` dependency)

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `getAds` method in `AdServiceImpl` catches `StatusRuntimeException` and forwards it via `responseObserver.onError(e)` (line 101). gRPC provides standard status codes (OK, INVALID_ARGUMENT, INTERNAL, UNAVAILABLE) which are machine-readable. However, there is no structured error body beyond the gRPC status code — no error code taxonomy, no retryable boolean, no detailed error message format using the gRPC rich error model (`com.google.rpc.ErrorInfo`). An agent receiving `INTERNAL` cannot determine whether to retry.
- **Gap**: No rich error model. Agents cannot distinguish retriable from terminal errors based on gRPC status alone.
- **Compensating Controls**:
  - Wrap agent tool calls with client-side error classification based on gRPC status codes (UNAVAILABLE → retry, INVALID_ARGUMENT → terminal)
  - Implement retry with exponential backoff for UNKNOWN/UNAVAILABLE status codes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement gRPC rich error model using `com.google.rpc.ErrorInfo` to include error codes, retryable flags, and detailed messages in error responses.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 98–101, catch block with `responseObserver.onError(e)`)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: Istio AuthorizationPolicies are disabled (`authorizationPolicies.create: false`). The Helm template defines an AuthorizationPolicy that would restrict callers to the `frontend` service account on the `/hipstershop.AdService/GetAds` path, but this policy is not deployed. No agent-specific service accounts are defined. No IAM policies or application-level RBAC. The K8s ServiceAccount for adservice exists (`serviceAccounts.create: true`) but provides no permission scoping without AuthorizationPolicy enforcement.
- **Gap**: No caller restriction at any layer. No agent-specific service accounts with tailored permissions. No per-RPC scoping.
- **Compensating Controls**:
  - Enable AuthorizationPolicies to activate the existing Helm template restricting callers to the frontend service account
  - Define agent-specific K8s ServiceAccounts and add them to the AuthorizationPolicy
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable `authorizationPolicies.create: true` in `values.yaml`. Create agent-specific service accounts with per-RPC AuthorizationPolicy rules scoping agent access to `GetAds`.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy template gated by flag), `src/main/java/hipstershop/AdService.java` (no application-level auth)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The application code has no action-level authorization. The gRPC server in `AdService.java` accepts all calls that reach it — no `ServerInterceptor` for authorization, no role checks, no permission validation. The Helm template defines an AuthorizationPolicy with per-path rules (`/hipstershop.AdService/GetAds`, method POST, port 9555), but this is disabled (`authorizationPolicies.create: false`). Without the mesh policy, all RPCs are accessible to any caller.
- **Gap**: No application-layer action-level authorization. No mesh-layer enforcement (disabled). If the mesh is bypassed or misconfigured, all RPCs are open.
- **Compensating Controls**:
  - Enable AuthorizationPolicies for mesh-level per-path enforcement
  - The service exposes only one RPC (`GetAds`), limiting the action surface
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable AuthorizationPolicies as immediate mitigation. Implement a gRPC `ServerInterceptor` for action-level authorization as defense in depth beyond the mesh layer.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no auth interceptor), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy template), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: No secrets or credentials are used by the service. The only environment variable is `PORT` (line 53 of `AdService.java`, default 9555). Ad data is hardcoded in-memory via `createAdsMap()`. No database connections, no external API calls, no Secrets Manager or Vault integration. No hardcoded credentials found in source code, Dockerfile, or configuration. No `.env` files.
- **Gap**: No formal credential management framework. While the service currently has no credentials to manage, there is no infrastructure for credential lifecycle management if credentials are introduced.
- **Compensating Controls**:
  - Credential-free architecture eliminates current secret rotation concerns
  - K8s ServiceAccount with Istio mTLS (when enabled) avoids hardcoded credentials
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Maintain credential-free architecture. If credentials are introduced, use K8s Secrets with external secrets operator or AWS Secrets Manager.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 53, `System.getenv().getOrDefault("PORT", "9555")`), `Dockerfile` (no secrets), `build.gradle` (no secrets dependencies)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging exists. `log4j2.xml` configures JSON structured logging with Stackdriver trace placeholders (`traceId`, `spanId`), but `initTracing()` in `AdService.java` is a stub (TODO comment) — trace context is never populated. No principal attribution in any log output. Logs are ephemeral container stdout with no immutable storage configuration. No CloudTrail, no S3 with object lock, no CloudWatch log retention policies. Tracing is disabled in Helm values (`tracing: false`).
- **Gap**: No immutable audit trail. Cannot determine who called the service or attribute actions to specific agent identities. No immutable log storage.
- **Compensating Controls**:
  - Configure K8s log forwarding to immutable store (e.g., CloudWatch Logs with retention policy, S3 with Object Lock)
  - Enable Istio access logging for mesh-level request attribution
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add structured audit logging with caller identity (extracted from Istio mTLS peer identity when AUTH-Q1 is resolved). Forward to immutable store. Enable tracing to populate log correlation IDs.
- **Evidence**: `src/main/resources/log4j2.xml` (trace ID placeholders never populated), `src/main/java/hipstershop/AdService.java` (lines 166–176, initTracing stub), `helm-chart/values.yaml` (`tracing: false`)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism exists. There are no agent-specific identities to suspend (AUTH-Q1 blocker). The Helm template includes an AuthorizationPolicy that could restrict callers, but it is disabled. No API key revocation, no service account disable mechanism, no kill switch for individual agent instances. The only way to block a caller would be to modify the Helm values and redeploy.
- **Gap**: No mechanism to immediately suspend a misbehaving agent without redeployment. No agent-specific identities exist to target.
- **Compensating Controls**:
  - When AuthorizationPolicies are enabled, removing an agent's service account principal from the policy blocks access
  - K8s NetworkPolicy (when enabled) can block specific pod selectors
- **Remediation Timeline**: 30–60 days
- **Recommendation**: After resolving AUTH-Q1, implement agent-specific K8s ServiceAccounts. Use AuthorizationPolicy updates to suspend individual agent identities without full redeployment.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy template)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: Tracing is disabled (`googleCloudOperations.tracing: false` in `helm-chart/values.yaml`). The `initTracing()` method in `AdService.java` (lines 166–176) is a stub with TODO comments — no OpenTelemetry SDK is initialized, no trace context is propagated. The `log4j2.xml` configures JSON structured logging with Stackdriver trace placeholders (`traceId`, `spanId`, `traceSampled`), but these context values are never populated because tracing is not initialized. Logs are structured JSON (good) but lack correlation IDs. No `traceparent` header propagation. No X-Ray or OpenTelemetry instrumentation.
- **Gap**: No distributed tracing. Structured logs exist but lack trace correlation. Agent-initiated requests cannot be traced through the service.
- **Compensating Controls**:
  - JSON structured logging provides basic log analysis capability
  - Istio sidecar (when enabled) provides mesh-level trace context independent of application instrumentation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement OpenTelemetry Java SDK instrumentation. Initialize the tracing exporter in `initTracing()`. Configure `log4j2.xml` MDC context to populate `traceId` and `spanId` from active spans.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 166–176, `initTracing()` stub with TODO), `src/main/resources/log4j2.xml` (trace placeholders never populated), `helm-chart/values.yaml` (`tracing: false`)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration exists. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. The Helm chart defines resource requests/limits (CPU: 200m–300m, memory: 180Mi–300Mi) and gRPC health probes (readiness and liveness on port 9555 with 20s initial delay, 15s period), but no error rate or latency alerting. Stats collection is stubbed out in `initStats()` (lines 155–163) with a TODO comment.
- **Gap**: No alerting on error rates or latency. Target system degradation will not be detected until agents start failing.
- **Compensating Controls**:
  - gRPC health probes provide basic availability detection via K8s
  - Istio sidecar metrics (when enabled) can feed Prometheus alerting
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Prometheus alerting rules for gRPC error rates and p99 latency on the `GetAds` RPC. Integrate with alerting system (PagerDuty, OpsGenie, or CloudWatch).
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 155–163, `initStats()` stub), `helm-chart/templates/adservice.yaml` (health probes only, no alerting)

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: RISK
- **Finding**: The proto file uses `package hipstershop` with no version suffix (not `hipstershop.v1`). No `buf.yaml` or `buf.lock` exists — no breaking change detection via `buf breaking`. No changelog or deprecation notices. No consumer-driven contract tests (Pact). The `build.gradle` generates Java stubs from the proto but has no schema validation step. The CI pipeline (`ci-pr.yaml`) runs Go and C# unit tests but no proto compatibility checks. Proto changes could silently break agent tool bindings.
- **Gap**: No proto versioning. No breaking change detection in CI. Schema changes can silently break agent integrations.
- **Compensating Controls**:
  - Pin agent tool definitions to the current proto schema with explicit integration tests
  - The proto file is checked into source control, providing change history via git
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add version suffix to proto package (`hipstershop.v1`). Integrate `buf breaking` into CI to detect breaking changes. Establish a deprecation policy for proto field changes.
- **Evidence**: `src/main/proto/demo.proto` (line 17, `package hipstershop` — no version), repository-wide: no `buf.yaml` found, `.github/workflows/ci-pr.yaml` (no proto validation step)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Infrastructure is defined as Helm charts (`helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`) and Terraform (`/.github/terraform/`). The Helm chart defines the Deployment, Service, NetworkPolicy, Sidecar, and AuthorizationPolicy templates. GitHub Actions CI includes `helm-chart-ci.yaml` and `terraform-validate-ci.yaml` for validation. PR-based review is enforced via GitHub pull request workflow. However, no drift detection is configured — no AWS Config rules, no ArgoCD sync status, no Flux reconciliation monitoring.
- **Gap**: IaC exists and is subject to PR review, but no drift detection monitors whether deployed state matches the Helm chart definitions.
- **Compensating Controls**:
  - Helm chart templates provide declarative infrastructure definition
  - GitHub PR workflow enforces peer review on IaC changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement GitOps with ArgoCD or Flux to detect and alert on drift between Helm chart definitions and deployed state.
- **Evidence**: `helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/terraform/`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: CI/CD exists via GitHub Actions (`ci-pr.yaml`) and Cloud Build (`cloudbuild.yaml`). The PR workflow runs Go and C# unit tests, deploys to a staging GKE cluster via Skaffold, and runs smoke tests via the load generator. However, there are no API contract tests — no Pact tests, no proto compatibility checks, no gRPC integration tests for the ad service specifically. The Java ad service has no test directory. The CI pipeline does not validate proto schema compatibility.
- **Gap**: No API contract testing for the ad service. No proto breaking change detection. Agent-facing API changes are not validated before production.
- **Compensating Controls**:
  - Smoke tests via load generator provide basic end-to-end validation
  - Staging deployment in CI provides a pre-production validation environment
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC integration tests for the `GetAds` RPC. Integrate `buf breaking` for proto compatibility checks. Add contract tests validating request/response schemas.
- **Evidence**: `.github/workflows/ci-pr.yaml` (no Java/ad service tests), `cloudbuild.yaml` (Skaffold deploy, no contract tests), `src/adservice/` (no test directory)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a gRPC API defined in `src/main/proto/demo.proto`. The `AdService` has a single RPC: `GetAds(AdRequest) returns (AdResponse)`. This is a well-defined, typed interface — not direct database access, file-based exchange, or UI automation. The proto IDL serves as both the interface definition and the code generation source.
- **Implication**: The gRPC interface is agent-consumable. Agent tool definitions can be generated directly from the proto file. gRPC's strong typing reduces integration ambiguity compared to untyped REST endpoints.
- **Recommendation**: No action required. The gRPC proto interface is a well-documented, strongly-typed API surface suitable for agent tool binding.
- **Evidence**: `src/main/proto/demo.proto` (lines 253–268, AdService definition), `src/main/java/hipstershop/AdService.java` (AdServiceImpl class)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The service has no write operations. `GetAds` is a read-only RPC that returns ads based on context keywords from a static in-memory map. Idempotency is inherently satisfied — repeated `GetAds` calls with the same context keys return the same ad set (deterministic lookup from `ImmutableListMultimap`), with random fallback when no matching category is found.
- **Implication**: No idempotency concern for the current read-only API surface.
- **Recommendation**: No action required for current scope.
- **Evidence**: `src/main/proto/demo.proto` (GetAds RPC — read-only), `src/main/java/hipstershop/AdService.java` (getAdsByCategory returns from ImmutableListMultimap)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Responses are serialized as Protocol Buffers (binary format) over gRPC. The `AdResponse` message contains a repeated `Ad` field, where each `Ad` has `redirect_url` (string) and `text` (string). Protobuf is strongly typed and machine-readable. gRPC clients auto-deserialize responses using generated stubs. JSON transcoding is not configured but could be added via `grpc-gateway` or Envoy.
- **Implication**: Protobuf is highly structured and efficient for machine consumption. LLM-based agents may need a JSON transcoding layer if they cannot consume binary protobuf directly.
- **Recommendation**: Consider adding gRPC-JSON transcoding via Envoy or `grpc-gateway` if agents require JSON responses.
- **Evidence**: `src/main/proto/demo.proto` (AdResponse, Ad message definitions), `build.gradle` (protobuf plugin configuration)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limiting is configured at any layer. No `X-RateLimit-Remaining` or `Retry-After` headers in gRPC responses. gRPC does not natively support rate limit headers in the HTTP/2 transport. No rate limit documentation exists.
- **Implication**: Agents calling at machine speed have no rate limit feedback. For a stateless-utility serving static data, the risk is lower than for stateful services.
- **Recommendation**: Document expected throughput capacity. Consider adding gRPC server-side rate limiting via an interceptor when AuthorizationPolicies are enabled.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no rate limiting), `helm-chart/templates/adservice.yaml` (no rate limit config)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation exists. No JWT parsing, no OAuth2 token exchange, no `X-User-Id` headers, no on-behalf-of flows. The `GetAds` RPC accepts only `context_keys` (product category strings) — no user identity context in the request schema. The service does not need caller identity to serve ads.
- **Implication**: For a stateless-utility serving public ad categories, identity propagation has minimal security impact. The service does not personalize responses per user. Archetype calibration: downgraded to INFO for stateless-utility.
- **Recommendation**: No action required for current scope.
- **Evidence**: `src/main/proto/demo.proto` (AdRequest contains only `context_keys`, no user identity), `src/main/java/hipstershop/AdService.java` (getAds processes only context keys)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The service has no write operations and no multi-step workflows. `GetAds` is a stateless read from an in-memory map. Compensation is not applicable to a read-only, stateless service.
- **Implication**: No compensation concern for the current read-only scope.
- **Recommendation**: No action required for current scope.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (read-only getAds, no state mutations)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: INFO
- **Finding**: No rate limiting is enforced at any layer. The Helm chart defines resource limits (CPU: 300m, memory: 300Mi) which provide a coarse resource ceiling but not request-level throttling. NetworkPolicies are disabled. For a stateless-utility serving static data with no external dependencies, the blast radius of a runaway agent loop is limited to pod resource exhaustion — no data corruption, no cascading failures.
- **Implication**: A runaway agent loop could exhaust pod resources but cannot corrupt data or cascade to external dependencies.
- **Recommendation**: Consider adding gRPC server-side rate limiting via interceptor as defense in depth.
- **Evidence**: `helm-chart/templates/adservice.yaml` (resource limits only), `helm-chart/values.yaml` (`networkPolicies.create: false`)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The service has no write operations. No records can be modified, no spend can be triggered, no deletions can occur. Transaction limits are not applicable to a read-only service serving static data.
- **Implication**: No blast radius concern for read-only scope.
- **Recommendation**: No action required for current scope.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (read-only operations only)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: The CI pipeline (`ci-pr.yaml`) deploys PR builds to a staging GKE cluster (`prs-gke-cluster` in `us-central1`, project `online-boutique-ci`) with per-PR namespaces (`pr${PR_NUMBER}`). The staging environment runs the full microservices stack via Skaffold with smoke tests via the load generator. This provides a production-equivalent environment for agent testing.
- **Implication**: A staging environment exists for agent testing. Per-PR namespaces provide isolation.
- **Recommendation**: Document the staging environment as the designated agent testing environment. Consider adding seed data scripts for reproducible test scenarios.
- **Evidence**: `.github/workflows/ci-pr.yaml` (staging GKE deployment with per-PR namespaces, smoke tests)

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: The ad service serves public, non-sensitive data. The `createAdsMap()` method in `AdService.java` contains hardcoded ad entries with product redirect URLs and promotional text (e.g., "Hairdryer for sale. 50% off."). Ad categories are public product categories (clothing, accessories, footwear, hair, decor, kitchen). No PII, PHI, financial records, or credentials are stored or processed. No `DATA_CLASSIFICATION.md` exists in the repository. The `AdRequest` contains only `context_keys` (category strings) — no user identity or sensitive fields.
- **Implication**: Ad data is public promotional content with no sensitivity classification needed. No data access controls are required beyond standard service authentication.
- **Recommendation**: Create a `DATA_CLASSIFICATION.md` documenting that ad service data is classified as PUBLIC.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 119–157, createAdsMap with public ad data), `src/main/proto/demo.proto` (AdRequest/AdResponse — no sensitive fields)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The ad data is hardcoded in application source code — not stored in a database or external data store. The data consists of public promotional text and product URLs with no PII, no GDPR-regulated personal data, and no sector-specific regulated content. No data residency requirements apply to public ad categories.
- **Implication**: No data residency concern. Public ad data has no regulatory residency requirements.
- **Recommendation**: No action required. Document the PUBLIC classification in a data residency assessment if required by organizational policy.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (hardcoded ad data, no external data store), `src/main/proto/demo.proto` (no PII fields)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: The service processes no PII. Log output includes ad request context keys (product categories) and gRPC status information. No customer data, user IDs, email addresses, or other PII appears in log output.
- **Implication**: No PII redaction concern. The service does not process or log any personally identifiable information.
- **Recommendation**: No action required.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 92, logs context keys only), `src/main/resources/log4j2.xml` (JSON layout)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: Ad data is hardcoded in source code with fixed quality — no null values, no stale data, no external data source that could degrade. The `ImmutableListMultimap` is populated at class load time and never changes. Data quality is deterministic and 100% complete by construction.
- **Implication**: No data quality concern. Static hardcoded data has perfect quality by definition.
- **Recommendation**: No action required for current scope.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 119–157, createAdsMap — static, complete data)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Proto field names are human-readable and semantically meaningful: `context_keys`, `redirect_url`, `text`, `ads`. No legacy abbreviations or codes. The Java class names follow standard conventions. The in-memory map uses readable category keys: "clothing", "accessories", "footwear", "hair", "decor", "kitchen".
- **Implication**: Field names are LLM-friendly. An agent can reason about the API surface without a data dictionary.
- **Recommendation**: No action required.
- **Evidence**: `src/main/proto/demo.proto` (field names), `src/main/java/hipstershop/AdService.java` (category keys in createAdsMap)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. The proto file serves as the de facto schema documentation. No AWS Glue Data Catalog, no Collibra, no DataHub.
- **Implication**: For a simple stateless-utility, the proto file provides sufficient schema documentation.
- **Recommendation**: No action required for current scope.
- **Evidence**: `src/main/proto/demo.proto` (schema documentation)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published. The `initStats()` method (lines 155–163) is a stub with a TODO comment. No ad impression tracking, no click-through rate metrics, no ad relevance scoring.
- **Implication**: When agents consume the ad service, there is no way to measure whether agent-selected ads produce good business outcomes.
- **Recommendation**: Implement ad impression and click-through metrics to measure agent interaction quality.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 155–163, initStats stub)

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: Deployment uses Skaffold with Cloud Build for production and GitHub Actions for PR staging. Helm chart supports `helm rollback` natively. The Kubernetes Deployment uses standard rolling update strategy. No canary deployment, no blue/green configuration, no automatic rollback triggers. Rollback requires manual `helm rollback` or `skaffold` redeployment. However, the rollback capability exists — the gap is automation, not capability.
- **Implication**: Manual rollback via Helm is available and functional. For a P2 stateless-utility, manual rollback within 15–30 minutes is achievable.
- **Recommendation**: Consider Flagger or Argo Rollouts for automated canary deployments with rollback as the service matures.
- **Evidence**: `helm-chart/Chart.yaml` (version 0.10.5), `helm-chart/templates/adservice.yaml` (Deployment with health probes), `cloudbuild.yaml` (Skaffold deploy)

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: No automated tests exist for the ad service. The `src/adservice/` directory contains no test directory, no test files, and no test dependencies in `build.gradle`. The CI pipeline runs Go and C# tests for other services but no Java tests for adservice. The smoke test via load generator provides basic end-to-end validation. Evaluated as INFO for stateless-utility archetype.
- **Implication**: No API test coverage means agent tool behavior cannot be validated against expected responses.
- **Recommendation**: Add gRPC unit tests for the `GetAds` RPC validating response format, category matching, and random fallback behavior.
- **Evidence**: `src/adservice/` (no test directory), `build.gradle` (no test dependencies), `.github/workflows/ci-pr.yaml` (no Java/adservice tests)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The service exposes a gRPC API defined in `src/main/proto/demo.proto`. The `AdService` has a single RPC: `GetAds(AdRequest) returns (AdResponse)`. This is a well-defined, typed interface using Protocol Buffers — not direct database access, file-based exchange, or UI automation.
- **Gap**: The proto file is a monolithic definition containing all 10 Online Boutique services. No standalone ad service spec exists.
- **Recommendation**: Consider extracting the `AdService` proto definition into a standalone file for independent versioning.
- **Evidence**: `src/main/proto/demo.proto` (lines 253–268), `src/main/java/hipstershop/AdService.java` (AdServiceImpl), `build.gradle` (protobuf plugin)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: The `demo.proto` file is a machine-readable IDL defining the `AdService` RPC, request/response messages, and field types. However, it is a monolithic file shared across all services. No OpenAPI, AsyncAPI, or Smithy model exists. gRPC server reflection is not enabled — the server builder adds only `AdServiceImpl` and `HealthStatusManager`, not `ProtoReflectionService`.
- **Gap**: No standalone machine-readable spec. No gRPC server reflection for runtime discovery.
- **Recommendation**: Enable gRPC server reflection. Consider extracting ad service proto definitions into a standalone file.
- **Evidence**: `src/main/proto/demo.proto`, `build.gradle` (`io.grpc:grpc-services`), `src/main/java/hipstershop/AdService.java` (server builder, lines 56–61)

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: The `getAds` method catches `StatusRuntimeException` and forwards it via `responseObserver.onError(e)`. gRPC provides standard status codes but no rich error model is implemented. No `com.google.rpc.ErrorInfo`, no retryable boolean, no error code taxonomy.
- **Gap**: No rich error model beyond gRPC status codes.
- **Recommendation**: Implement gRPC rich error model using `com.google.rpc.ErrorInfo` with error codes and retryable flags.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 98–101, catch block)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write operations exist. `GetAds` is read-only. Idempotency is inherently satisfied for reads from an immutable in-memory map.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action required.
- **Evidence**: `src/main/proto/demo.proto` (GetAds — read-only), `src/main/java/hipstershop/AdService.java` (ImmutableListMultimap)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Responses are Protocol Buffers (binary) over gRPC. `AdResponse` contains repeated `Ad` messages with `redirect_url` and `text` string fields. Strongly typed and machine-readable.
- **Gap**: Binary protobuf may require transcoding for LLM-based agents that expect JSON.
- **Recommendation**: Consider gRPC-JSON transcoding via Envoy or `grpc-gateway` if agents require JSON.
- **Evidence**: `src/main/proto/demo.proto` (AdResponse, Ad messages), `build.gradle` (protobuf plugin)

#### API-Q6: Asynchronous Operation Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has operations >30s OR long-running workflows
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q7: Event Emission for State Changes
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has state changes (stateful-crud, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### API-Q8: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limiting configured. No `X-RateLimit-Remaining` or `Retry-After` headers. gRPC does not natively support rate limit headers. No rate limit documentation.
- **Gap**: No rate limit feedback for agents.
- **Recommendation**: Document expected throughput capacity. Consider gRPC server-side rate limiting via interceptor.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no rate limiting), `helm-chart/templates/adservice.yaml` (no rate limit config)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: `ServerBuilder.forPort(port)` with no authentication interceptor, no TLS, no credential verification. AuthorizationPolicies disabled (`authorizationPolicies.create: false`). NetworkPolicies disabled (`networkPolicies.create: false`). Any network-reachable client can call `GetAds` without presenting credentials.
- **Gap**: No machine identity authentication at any layer. Agents cannot be identified or attributed.
- **Recommendation**: Enable Istio AuthorizationPolicies (`authorizationPolicies.create: true`) for mTLS-based caller identity. Implement gRPC `ServerInterceptor` for defense-in-depth.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 56, `ServerBuilder.forPort(port)`), `helm-chart/values.yaml` (`authorizationPolicies.create: false`, `networkPolicies.create: false`)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: AuthorizationPolicies disabled. The Helm template defines a policy restricting callers to the `frontend` service account on `/hipstershop.AdService/GetAds`, but it is not deployed. No agent-specific service accounts. No IAM policies or application-level RBAC.
- **Gap**: No caller restriction at any layer. No agent-specific permission scoping.
- **Recommendation**: Enable `authorizationPolicies.create: true`. Create agent-specific service accounts with per-RPC AuthorizationPolicy rules.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/adservice.yaml` (AuthorizationPolicy template)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No application-layer authorization. No `ServerInterceptor` for auth. AuthorizationPolicy with per-path rules exists in Helm template but is disabled. Without mesh enforcement, all RPCs are open.
- **Gap**: No action-level authorization at any layer.
- **Recommendation**: Enable AuthorizationPolicies. Implement gRPC `ServerInterceptor` for defense in depth.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (no auth interceptor), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. No JWT parsing, no token exchange, no user context headers. `AdRequest` contains only `context_keys` — no user identity. The service does not need caller identity to serve ads. Archetype calibration: downgraded to INFO for stateless-utility.
- **Gap**: No identity propagation, but not needed for public ad data.
- **Recommendation**: No action required for current scope.
- **Evidence**: `src/main/proto/demo.proto` (AdRequest — no user identity fields), `src/main/java/hipstershop/AdService.java` (processes only context keys)

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: No secrets or credentials used. Only environment variable is `PORT`. Ad data is hardcoded in-memory. No database connections, no external API calls, no Secrets Manager or Vault. No hardcoded credentials found.
- **Gap**: No credential management framework for future credential needs.
- **Recommendation**: Maintain credential-free architecture. Use K8s Secrets with external secrets operator if credentials are introduced.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 53, PORT only), `Dockerfile`, `build.gradle`

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No audit logging. `log4j2.xml` has trace placeholders but `initTracing()` is a stub. No principal attribution. Logs are ephemeral container stdout. No immutable storage. Tracing disabled (`tracing: false`).
- **Gap**: No immutable audit trail. No principal attribution. No immutable log storage.
- **Recommendation**: Add structured audit logging with caller identity. Forward to immutable store. Enable tracing.
- **Evidence**: `src/main/resources/log4j2.xml`, `src/main/java/hipstershop/AdService.java` (lines 166–176, initTracing stub), `helm-chart/values.yaml` (`tracing: false`)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism. No agent-specific identities exist (AUTH-Q1 blocker). AuthorizationPolicies disabled. Only way to block a caller is Helm value change and redeploy.
- **Gap**: No mechanism to immediately suspend a misbehaving agent.
- **Recommendation**: After resolving AUTH-Q1, implement agent-specific ServiceAccounts with AuthorizationPolicy-based suspension.
- **Evidence**: `helm-chart/values.yaml` (`authorizationPolicies.create: false`), `helm-chart/templates/adservice.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write operations. `GetAds` is stateless read from immutable in-memory map. Compensation not applicable.
- **Gap**: N/A — no write operations.
- **Recommendation**: No action required.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (read-only getAds)

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled AND service has persistent state
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has external dependencies (calls other services or external APIs)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: INFO
- **Finding**: No rate limiting at any layer. Resource limits (CPU: 300m, memory: 300Mi) provide a coarse ceiling. NetworkPolicies disabled. For a stateless-utility with no external dependencies, blast radius of runaway agent is limited to pod resource exhaustion.
- **Gap**: No request-level throttling.
- **Recommendation**: Consider gRPC server-side rate limiting via interceptor.
- **Evidence**: `helm-chart/templates/adservice.yaml` (resource limits), `helm-chart/values.yaml` (`networkPolicies.create: false`)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write operations. No records can be modified, no spend triggered, no deletions possible.
- **Gap**: N/A — read-only scope.
- **Recommendation**: No action required.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (read-only operations)

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service is P0 priority OR is on the critical path
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q2: Configurable Approval Gates ⚡
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: agent_scope is write-enabled
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: CI pipeline deploys PR builds to staging GKE cluster (`prs-gke-cluster`, `us-central1`, project `online-boutique-ci`) with per-PR namespaces. Full microservices stack deployed via Skaffold with smoke tests via load generator. Production-equivalent environment available for agent testing.
- **Gap**: No dedicated agent testing documentation. No seed data scripts for reproducible scenarios.
- **Recommendation**: Document staging environment as designated agent testing environment.
- **Evidence**: `.github/workflows/ci-pr.yaml` (staging deployment, smoke tests)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Ad data is public promotional content: product redirect URLs and promotional text hardcoded in `createAdsMap()`. Categories are public product categories (clothing, accessories, footwear, hair, decor, kitchen). No PII, PHI, financial records, or credentials. `AdRequest` contains only `context_keys` (category strings). No `DATA_CLASSIFICATION.md` exists.
- **Gap**: No formal data classification document, though data is clearly public.
- **Recommendation**: Create `DATA_CLASSIFICATION.md` documenting ad service data as PUBLIC.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 119–157, createAdsMap), `src/main/proto/demo.proto` (AdRequest/AdResponse)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Ad data is hardcoded in source code. Public promotional text with no PII, no GDPR-regulated data, no sector-specific regulated content. No data residency requirements apply.
- **Gap**: No formal data residency documentation.
- **Recommendation**: Document PUBLIC classification in data residency assessment if required by organizational policy.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (hardcoded ad data), `src/main/proto/demo.proto`

#### DATA-Q3: Selective Query Support
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has list/query endpoints with potentially unbounded results
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q4: System of Record Designations
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q5: Temporal Metadata and Freshness
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### DATA-Q6: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: No PII processed or logged. Log output includes ad request context keys (product categories) and gRPC status. No customer data, user IDs, or email addresses in logs.
- **Gap**: None — no PII to redact.
- **Recommendation**: No action required.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (line 92, logs context keys only), `src/main/resources/log4j2.xml`

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: Ad data is hardcoded with fixed quality. `ImmutableListMultimap` populated at class load time. No null values, no stale data, no external data source. Data quality is 100% complete by construction.
- **Gap**: None — static data has perfect quality.
- **Recommendation**: No action required.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 119–157, createAdsMap)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: RISK
- **Finding**: Proto uses `package hipstershop` with no version suffix (not `hipstershop.v1`). No `buf.yaml` or `buf.lock` — no breaking change detection. No changelog or deprecation notices. No consumer-driven contract tests. CI pipeline has no proto compatibility checks.
- **Gap**: No proto versioning. No breaking change detection in CI.
- **Recommendation**: Add version suffix to proto package (`hipstershop.v1`). Integrate `buf breaking` into CI.
- **Evidence**: `src/main/proto/demo.proto` (line 17, `package hipstershop`), no `buf.yaml` found, `.github/workflows/ci-pr.yaml`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Proto field names are human-readable: `context_keys`, `redirect_url`, `text`, `ads`. Java classes follow standard conventions. Category keys are readable: "clothing", "accessories", "footwear".
- **Gap**: None — naming is clear and semantic.
- **Recommendation**: No action required.
- **Evidence**: `src/main/proto/demo.proto`, `src/main/java/hipstershop/AdService.java`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. The proto file serves as de facto schema documentation. No Glue Data Catalog, Collibra, or DataHub.
- **Gap**: No formal metadata layer beyond the proto file.
- **Recommendation**: No action required. Proto file is sufficient for this service's complexity.
- **Evidence**: `src/main/proto/demo.proto`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: Tracing disabled (`tracing: false` in values.yaml). `initTracing()` is a stub with TODO. `log4j2.xml` has JSON structured logging with trace placeholders (`traceId`, `spanId`) that are never populated. No OpenTelemetry SDK, no X-Ray, no `traceparent` propagation.
- **Gap**: No distributed tracing. Structured logs lack trace correlation.
- **Recommendation**: Implement OpenTelemetry Java SDK. Initialize tracing exporter. Populate log4j2 MDC context.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 166–176, initTracing stub), `src/main/resources/log4j2.xml`, `helm-chart/values.yaml` (`tracing: false`)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. No CloudWatch alarms, no Prometheus rules, no PagerDuty integration. Health probes exist (gRPC on port 9555) but no error rate or latency alerting. `initStats()` is a stub with TODO.
- **Gap**: No alerting on error rates or latency.
- **Recommendation**: Configure Prometheus alerting rules for gRPC error rates and p99 latency.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 155–163, initStats stub), `helm-chart/templates/adservice.yaml` (health probes only)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No custom business metrics. `initStats()` is a stub. No ad impression tracking, no click-through metrics, no ad relevance scoring.
- **Gap**: No business outcome measurement for agent interactions.
- **Recommendation**: Implement ad impression and click-through metrics.
- **Evidence**: `src/main/java/hipstershop/AdService.java` (lines 155–163, initStats stub)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Infrastructure defined as Helm charts and Terraform. GitHub Actions CI includes `helm-chart-ci.yaml` and `terraform-validate-ci.yaml`. PR-based review enforced. No drift detection (no AWS Config, no ArgoCD, no Flux).
- **Gap**: IaC exists with PR review, but no drift detection.
- **Recommendation**: Implement GitOps with ArgoCD or Flux for drift detection.
- **Evidence**: `helm-chart/templates/adservice.yaml`, `helm-chart/values.yaml`, `.github/workflows/helm-chart-ci.yaml`, `.github/terraform/`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI/CD exists via GitHub Actions and Cloud Build. PR workflow runs Go/C# tests and staging deployment with smoke tests. No API contract tests for ad service. No proto compatibility checks. No Java tests. No test directory in `src/adservice/`.
- **Gap**: No API contract testing for ad service. No proto breaking change detection.
- **Recommendation**: Add gRPC integration tests for `GetAds`. Integrate `buf breaking` for proto compatibility.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `cloudbuild.yaml`, `src/adservice/` (no test directory)

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: Deployment via Skaffold/Cloud Build and Helm. Helm supports `helm rollback` natively. K8s Deployment uses rolling update. No canary, no blue/green, no automatic rollback triggers. Rollback is manual but the capability exists.
- **Gap**: No automated rollback triggers. Manual rollback only.
- **Recommendation**: Consider Flagger or Argo Rollouts for automated canary deployments.
- **Evidence**: `helm-chart/Chart.yaml`, `helm-chart/templates/adservice.yaml`, `cloudbuild.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: No automated tests for ad service. No test directory, no test files, no test dependencies. CI runs tests for other services only. Smoke test via load generator provides basic end-to-end validation. Evaluated as INFO for stateless-utility archetype.
- **Gap**: No API test coverage for ad service.
- **Recommendation**: Add gRPC unit tests for `GetAds` RPC.
- **Evidence**: `src/adservice/` (no test directory), `build.gradle` (no test dependencies), `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent data stores
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `helm-chart/templates/adservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q7, OBS-Q2, ENG-Q1, ENG-Q3, API-Q8, STATE-Q5 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, OBS-Q1, STATE-Q5, ENG-Q1 |
| `helm-chart/Chart.yaml` | ENG-Q3 |
| `.github/terraform/` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/main/java/hipstershop/AdService.java` | API-Q1, API-Q2, API-Q3, API-Q4, API-Q8, AUTH-Q1, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, STATE-Q1, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q2, OBS-Q3, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `src/main/proto/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, AUTH-Q4, DATA-Q1, DATA-Q2, DISC-Q1, DISC-Q2, DISC-Q3 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | HITL-Q3, DISC-Q1, ENG-Q2, ENG-Q4 |
| `.github/workflows/helm-chart-ci.yaml` | ENG-Q1 |
| `cloudbuild.yaml` | ENG-Q2, ENG-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | AUTH-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `build.gradle` | API-Q2, API-Q5, AUTH-Q5, ENG-Q4 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `src/main/resources/log4j2.xml` | AUTH-Q6, OBS-Q1, DATA-Q6 |
| `settings.gradle` | (metadata — `rootProject.name = 'hipstershop'`) |
