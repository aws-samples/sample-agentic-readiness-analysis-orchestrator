# Agentic Readiness Assessment Report

**Target**: services/microservices-demo/src/recommendationservice
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P1
**Tags**: python, grpc, ml, recommendations
**Context**: Python gRPC service providing product recommendations based on cart contents.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 24 | **INFOs**: 23

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 24 |
| INFO | 23 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server in `recommendation_server.py` uses `grpc.insecure_channel()` to connect to ProductCatalogService and `server.add_insecure_port()` to listen for incoming requests. There is no TLS, no mTLS, no OAuth2 client credentials flow, no API key authentication, and no service account authentication at the application layer. The Kubernetes ServiceAccount (`recommendationservice`) defined in `kubernetes-manifests/recommendationservice.yaml` provides pod-level identity for Kubernetes RBAC but does not authenticate incoming gRPC callers. The Istio AuthorizationPolicy in `helm-chart/templates/recommendationservice.yaml` restricts source principals to the frontend service at the mesh level, but this is network-level enforcement — it does not attribute authenticated principals in application audit logs. No audit log entry identifies which agent or caller made a request.
- **Gap**: No application-level machine identity authentication. No mechanism to authenticate and attribute agent identities. No audit log attribution for the calling principal.
- **Remediation**:
  - **Immediate**: Introduce mTLS via Istio service mesh (enable `authorizationPolicies.create=true` and `sidecars.create=true` in Helm values) to enforce mutual authentication between services. This provides transport-level identity attribution without application code changes.
  - **Target State**: gRPC server authenticates incoming calls via mTLS or JWT bearer tokens, and every request is logged with the authenticated principal identity. Agent-specific service accounts are distinguishable in audit logs.
  - **Estimated Effort**: Medium (2–4 weeks for mTLS via Istio; 4–8 weeks for application-level JWT auth)
  - **Dependencies**: Istio must be deployed and configured in the cluster. AUTH-Q7 (audit logging) depends on this blocker being resolved first.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (lines 99–100: `grpc.insecure_channel`, line 108: `server.add_insecure_port`), `kubernetes-manifests/recommendationservice.yaml`, `helm-chart/templates/recommendationservice.yaml` (AuthorizationPolicy section)

### DATA-Q1: Sensitive Data Classification

- **Severity**: BLOCKER
- **Finding**: The `ListRecommendationsRequest` message in `protos/demo.proto` includes a `user_id` field (string type). This field is passed into the service in every request and could constitute PII depending on the format (e.g., email address, account number). The service code in `recommendation_server.py` receives `request.user_id` but does not use it for filtering — it only uses `request.product_ids` to exclude already-carted products. No data classification tags exist on any data field. No field-level encryption is applied. No PII detection tools (e.g., Amazon Macie) are integrated. The proto file contains no annotations or comments marking `user_id` as sensitive. No data classification policy or documentation was found in the repository.
- **Gap**: No data classification at the field level. `user_id` is unclassified and unprotected. No controls prevent an agent from retrieving or forwarding `user_id` without explicit authorization.
- **Remediation**:
  - **Immediate**: Classify all data fields in the proto definition. Mark `user_id` as PII. Add a data classification document to the repository. Evaluate whether `user_id` needs to be passed to the recommendation service at all (currently unused in the recommendation logic).
  - **Target State**: All data fields have classification tags (PII, sensitive, public). Field-level access controls prevent agents from accessing PII without explicit authorization. `user_id` is either removed from the request (since it is unused) or access-controlled.
  - **Estimated Effort**: Low (1–2 weeks for classification; 2–4 weeks for access controls)
  - **Dependencies**: None. This can be resolved independently.
- **Evidence**: `protos/demo.proto` (ListRecommendationsRequest message with `user_id` field), `src/recommendationservice/recommendation_server.py` (line 72: `request.product_ids` used, `request.user_id` received but unused)

## RISKs — Proceed with Compensating Controls

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The `ListRecommendations` method in `recommendation_server.py` has no try/except block and no structured error response handling. If `ProductCatalogService.ListProducts()` fails, the exception propagates unhandled through gRPC, which returns a generic `UNKNOWN` status code. The base class in `demo_pb2_grpc.py` returns `UNIMPLEMENTED` for unoverridden methods. No custom error codes, retryable booleans, or error category fields are defined in the proto response.
- **Gap**: No structured error responses beyond default gRPC status codes. No error code taxonomy. No retryable/non-retryable distinction for agents.
- **Compensating Controls**:
  - Agents can map gRPC status codes to retry behavior (e.g., UNAVAILABLE → retry, INVALID_ARGUMENT → do not retry)
  - Wrap agent tool calls with client-side error classification logic
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add try/except in `ListRecommendations` to catch gRPC errors from ProductCatalogService, return structured gRPC status codes (e.g., `UNAVAILABLE` for downstream failures), and add error metadata via gRPC trailing metadata.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (ListRecommendations method, lines 67–80), `demo_pb2_grpc.py` (base class returning UNIMPLEMENTED)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: The proto package is `hipstershop` with no version suffix (e.g., not `hipstershop.v1`). The gRPC service path is `/hipstershop.RecommendationService/ListRecommendations`. No versioning scheme in the URL, headers, or package name. No changelog file. No deprecation notices in the proto file or documentation.
- **Gap**: No API versioning. No deprecation policy. Breaking changes to the proto definition would silently break agent tool schemas.
- **Compensating Controls**:
  - Pin agent tool definitions to specific proto file git commit hashes
  - Monitor proto file changes in CI via git diff alerts
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt proto package versioning (e.g., `hipstershop.v1`). Add a CHANGELOG.md tracking API changes. Implement proto breaking-change detection in CI (e.g., `buf breaking`).
- **Evidence**: `protos/demo.proto` (package declaration: `package hipstershop;`)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No application-level permission model exists. The Kubernetes ServiceAccount `recommendationservice` has no fine-grained role bindings defined in the manifests. The Istio AuthorizationPolicy (when enabled) restricts which services can call the recommendation service but does not scope what actions a caller can perform within the service. All callers that pass network-level checks have full access to ListRecommendations.
- **Gap**: No scoped permissions at the application layer. An agent identity cannot be granted read-only access to specific resources — all authenticated callers have identical access.
- **Compensating Controls**:
  - Use Istio AuthorizationPolicy to restrict agent access to only the ListRecommendations RPC
  - Network-level isolation via NetworkPolicy limits blast radius
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement gRPC interceptors that check caller identity against a permission model. For the current single-RPC service, Istio AuthorizationPolicy provides adequate compensating control.
- **Evidence**: `kubernetes-manifests/recommendationservice.yaml` (ServiceAccount), `helm-chart/templates/recommendationservice.yaml` (AuthorizationPolicy)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: The service has a single RPC (ListRecommendations) with no permission checks in the application code. The Istio AuthorizationPolicy in `helm-chart/templates/recommendationservice.yaml` restricts to the specific operation path `/hipstershop.RecommendationService/ListRecommendations` and method `POST` on port `8080`. This provides action-level restriction at the mesh layer but not at the application layer.
- **Gap**: No application-level action-level authorization. Authorization depends entirely on Istio mesh configuration (disabled by default: `authorizationPolicies.create: false`).
- **Compensating Controls**:
  - Enable Istio AuthorizationPolicies (`authorizationPolicies.create=true` in Helm values)
  - For a single read-only RPC, action-level auth is less critical than for multi-operation services
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable Istio AuthorizationPolicies in production. Consider adding gRPC server interceptors for defense-in-depth.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml` (AuthorizationPolicy), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: The `ListRecommendationsRequest` proto message includes a `user_id` field, but this is an opaque string — not a verified identity from a JWT or OAuth token. There is no JWT parsing middleware, no OAuth2 on-behalf-of flow, and no token exchange mechanism. The `user_id` is passed by the caller without verification, meaning any caller can impersonate any user.
- **Gap**: No identity propagation. `user_id` is an unverified string field, not an authenticated identity claim.
- **Compensating Controls**:
  - Restrict callers to the frontend service via Istio AuthorizationPolicy (only the frontend can set user_id)
  - For read-only agents, identity propagation is less critical since no data mutation occurs
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement JWT-based identity propagation where the frontend passes a verified token. The recommendation service should validate the token and extract user_id from claims rather than trusting the raw field.
- **Evidence**: `protos/demo.proto` (ListRecommendationsRequest: `string user_id = 1`), `src/recommendationservice/recommendation_server.py` (user_id received but unverified)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No distinction exists between an agent acting under its own identity and an agent acting on behalf of a user. There is only one authentication path (none at the application level). No separate IAM roles, API keys, or auth flows for different agent modes. No audit log fields distinguish the two modes.
- **Gap**: Cannot differentiate agent-as-self from agent-on-behalf-of-user access patterns.
- **Compensating Controls**:
  - For a read-only recommendation service, the distinction is less critical — recommendations are not user-privileged
  - Use gRPC metadata headers to pass agent-mode context for logging purposes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Define separate Istio/Kubernetes ServiceAccounts for agent-as-self and agent-on-behalf-of-user access. Log the access mode in structured logs.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (no auth differentiation), `protos/demo.proto` (single request type for all callers)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: No secrets management system (AWS Secrets Manager, HashiCorp Vault) is integrated. The service uses environment variables for configuration: `PRODUCT_CATALOG_SERVICE_ADDR`, `PORT`, `ENABLE_TRACING`, `COLLECTOR_SERVICE_ADDR`, `DISABLE_PROFILER`. None of these are secrets. The gRPC channel is insecure (`grpc.insecure_channel`), so there are no TLS certificates to manage. No hardcoded passwords, API keys, or credentials were found in the codebase. However, the absence of any credential management infrastructure means that when authentication is introduced (AUTH-Q1 remediation), there is no framework for managing those credentials.
- **Gap**: No secrets management infrastructure. When credentials are introduced for authentication, rotation and secure storage must be built from scratch.
- **Compensating Controls**:
  - Currently no secrets exist, so the immediate risk is low
  - Kubernetes Secrets can serve as an interim solution when credentials are introduced
- **Remediation Timeline**: 30–60 days (aligned with AUTH-Q1 remediation)
- **Recommendation**: Deploy a secrets management solution (e.g., External Secrets Operator with GCP Secret Manager) before introducing authentication credentials.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (env vars for non-secret config), `kubernetes-manifests/recommendationservice.yaml` (env section — no secrets referenced)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured JSON logging is implemented via `logger.py` using `pythonjsonlogger`. The `CustomJsonFormatter` adds `timestamp` and `severity` fields. The `ListRecommendations` handler logs `product_ids` returned but does NOT log the authenticated principal (because no authentication exists — see AUTH-Q1). No CloudTrail or equivalent immutable log storage is configured. No S3 bucket with object lock. No CloudWatch log retention policies defined in IaC. Logs are written to stdout and captured by the Kubernetes container runtime, but immutability is not guaranteed.
- **Gap**: Logs do not include authenticated principal identity. No immutable log storage. No tamper-evident log chain.
- **Compensating Controls**:
  - Container stdout logs are captured by GKE logging (Cloud Logging) which provides retention but not immutability guarantees
  - For read-only agents, audit logging is less critical than for write-enabled agents
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add caller identity to log entries (once AUTH-Q1 is resolved). Configure log sink to immutable storage (e.g., Cloud Storage with bucket lock, or Cloud Logging with locked retention policies).
- **Evidence**: `src/recommendationservice/logger.py` (CustomJsonFormatter), `src/recommendationservice/recommendation_server.py` (line 78: logs product_ids only)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No mechanism exists to suspend or revoke individual agent identities. No API key system, no OAuth2 client deactivation, no IAM role disable. The Istio AuthorizationPolicy (when enabled) restricts by Kubernetes ServiceAccount — disabling an agent would require deleting or modifying the ServiceAccount or Istio policy, which is a cluster-level operation rather than an application-level action.
- **Gap**: Cannot suspend individual agent identities without cluster-level changes.
- **Compensating Controls**:
  - Istio AuthorizationPolicy can be updated to block specific service accounts
  - Kubernetes NetworkPolicy can isolate a misbehaving agent pod
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Implement API key-based authentication with a revocation endpoint, or use a centralized identity provider (e.g., GCP IAP, Cognito) with instant deactivation capability.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml` (AuthorizationPolicy — cluster-level control), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The service is stateless and read-only. The single RPC `ListRecommendations` fetches products from ProductCatalogService, filters, and returns a random sample. No multi-step write operations exist. No saga pattern, two-phase commit, or compensating transactions are needed for the current functionality.
- **Gap**: No compensation or rollback mechanism. This is acceptable for the current stateless read-only service but would become a blocker if write operations are added.
- **Compensating Controls**:
  - The service is inherently safe — failed reads have no side effects
  - If write operations are added in the future, implement compensation patterns before enabling write-enabled agent scope
- **Remediation Timeline**: Deferred (only needed if write operations are introduced)
- **Recommendation**: Document the stateless nature of the service. If write operations are added, implement saga/compensation patterns before changing agent_scope to write-enabled.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (ListRecommendations — read-only logic)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: The gRPC channel to ProductCatalogService is created with `grpc.insecure_channel(catalog_addr)` in `recommendation_server.py` with no timeout, no retry policy, no circuit breaker, and no exponential backoff. If ProductCatalogService is unavailable, `ListRecommendations` will block until the gRPC default deadline and then fail with an unstructured error. No resilience libraries (Resilience4j, Polly, tenacity) are imported. No fallback behavior (e.g., return cached recommendations) exists.
- **Gap**: No circuit breaker or resilience patterns on the ProductCatalogService dependency. A downstream failure cascades directly to all recommendation requests.
- **Compensating Controls**:
  - gRPC has built-in deadline propagation — callers can set deadlines to prevent unbounded blocking
  - Istio can provide circuit breaking at the mesh level (requires Istio deployment)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC channel options with timeout (`grpc.insecure_channel(addr, options=[('grpc.keepalive_timeout_ms', 5000)])`). Implement retry with exponential backoff using `tenacity` or gRPC retry policies. Add a circuit breaker pattern that returns an empty recommendation list when ProductCatalogService is unhealthy.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (line 99: `channel = grpc.insecure_channel(catalog_addr)` — no options)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting is configured at any layer. The gRPC server uses `ThreadPoolExecutor(max_workers=10)` which provides an implicit concurrency limit of 10 concurrent requests but is not a rate limiter. No API Gateway, no WAF rate rules, no application-level rate limiting middleware. The Kubernetes resource limits (200m CPU, 450Mi memory) provide resource bounds but not request-rate bounds.
- **Gap**: No rate limiting. A runaway agent could send thousands of requests per second, limited only by the 10-thread pool and Kubernetes resource quotas.
- **Compensating Controls**:
  - The 10-thread pool provides a natural backpressure mechanism — additional requests queue or are rejected
  - Kubernetes resource limits prevent the service from consuming unbounded cluster resources
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC server interceptors for rate limiting per caller identity. Alternatively, deploy an API Gateway (e.g., Envoy proxy) or Istio rate limiting in front of the service.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (line 103: `futures.ThreadPoolExecutor(max_workers=10)`), `kubernetes-manifests/recommendationservice.yaml` (resource limits)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: The Kubernetes deployment in `kubernetes-manifests/recommendationservice.yaml` specifies resource requests of 100m CPU / 220Mi memory and limits of 200m CPU / 450Mi memory. No Horizontal Pod Autoscaler (HPA) is defined. The default deployment creates a single replica. No load test results or capacity planning documentation exists. The gRPC server is limited to 10 concurrent workers. GKE Autopilot provides some auto-scaling at the node level but pod-level scaling requires an HPA.
- **Gap**: Single replica, no HPA, no load testing. The service is not sized or tested for agent-generated traffic patterns.
- **Compensating Controls**:
  - GKE Autopilot auto-scales nodes based on resource requests
  - Start agent pilot with low request rates and monitor resource utilization
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add an HPA targeting CPU utilization (e.g., 70%). Conduct load testing with agent-realistic traffic patterns. Increase `max_workers` for the gRPC server thread pool.
- **Evidence**: `kubernetes-manifests/recommendationservice.yaml` (resource limits, no HPA), `src/recommendationservice/recommendation_server.py` (max_workers=10)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The Terraform configuration in `variables.tf` defaults the deployment region to `us-central1`. No data residency requirements, GDPR references, LGPD compliance, or region-specific data storage configurations were found. The service processes `user_id` and `product_ids` — no data sovereignty constraints are documented. No cross-region replication is configured. If an agent transmits `user_id` to an LLM endpoint in a different region, there are no controls to prevent this.
- **Gap**: No data residency configuration or documentation. No controls on where data can be transmitted.
- **Compensating Controls**:
  - Deploy agent and LLM endpoint in the same region as the service (us-central1)
  - For read-only agents, data exposure risk is limited to product_ids (non-PII) if user_id is removed from responses
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Document data residency requirements. If user_id is classified as PII (DATA-Q1), implement controls to prevent cross-region transmission. Consider removing user_id from the request since it is unused by the recommendation logic.
- **Evidence**: `terraform/variables.tf` (region default: us-central1), `protos/demo.proto` (user_id in request)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: `ListRecommendations` accepts `product_ids` as a filter (products to exclude) and returns a maximum of 5 recommendations (hardcoded `max_responses = 5` in `recommendation_server.py`). There is no pagination, no cursor-based navigation, no sorting parameter, and no configurable limit. The response is always a list of up to 5 product IDs. For a recommendation service, the fixed result size is reasonable, but there is no mechanism for agents to request fewer or more results.
- **Gap**: Hardcoded result size. No pagination or configurable limit parameter.
- **Compensating Controls**:
  - The fixed 5-result limit naturally bounds response size and LLM context consumption
  - Agents can filter results client-side if needed
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `max_results` field to `ListRecommendationsRequest` proto message to allow callers to specify desired result count. This is a minor proto change with backward compatibility.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (line 68: `max_responses = 5`), `protos/demo.proto` (ListRecommendationsRequest)

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: The `ListRecommendationsResponse` proto message contains only `repeated string product_ids`. No timestamp fields (created_at, updated_at, event_time) are included in the response. The logger adds timestamps to log entries via `CustomJsonFormatter`, but these are not exposed in API responses. Agents receiving recommendations have no way to know when the product catalog data was last refreshed.
- **Gap**: No timestamps in API responses. Agents cannot determine data currency.
- **Compensating Controls**:
  - The service fetches live data from ProductCatalogService on every request, so results are always current at the time of the call
  - Agents can record their own request timestamps
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a `timestamp` field to `ListRecommendationsResponse` indicating when the recommendation was generated. Consider adding `catalog_last_updated` if ProductCatalogService exposes this information.
- **Evidence**: `protos/demo.proto` (ListRecommendationsResponse — product_ids only), `src/recommendationservice/logger.py` (timestamps in logs only)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness signaling exists. No `Cache-Control` headers (gRPC uses metadata, not HTTP headers). No `X-Data-Age` equivalent in gRPC trailing metadata. No `last_refreshed` field in the response. The service calls `ProductCatalogService.ListProducts()` on every request (no caching), so data is always fresh, but this freshness is not communicated to the caller.
- **Gap**: No freshness signaling. Agents cannot determine whether recommendations are based on current or stale data.
- **Compensating Controls**:
  - Since the service always fetches live data, staleness risk is low in practice
  - Document the always-fresh behavior in the service documentation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC response metadata indicating data freshness (e.g., `x-data-source: live`, `x-response-generated-at: <timestamp>`).
- **Evidence**: `src/recommendationservice/recommendation_server.py` (line 70: `cat_response = product_catalog_stub.ListProducts(demo_pb2.Empty())` — live call, no caching)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: The protobuf schema in `protos/demo.proto` defines all message types and service RPCs with field types and numbers. This serves as the schema documentation. The proto file is version-controlled in the git repository. However, the proto package (`hipstershop`) has no version suffix. No schema registry (e.g., Buf Schema Registry, Confluent Schema Registry) is used. No database migration files exist (service is stateless). No schema changelog tracks changes to the proto definition.
- **Gap**: No schema versioning beyond git history. No schema registry. No breaking-change detection.
- **Compensating Controls**:
  - Git history provides an implicit version trail for proto changes
  - Proto field numbers provide backward compatibility (new fields get new numbers)
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add proto versioning (`hipstershop.v1`). Integrate `buf` or similar tool for schema linting and breaking-change detection in CI. Consider publishing the proto to a schema registry.
- **Evidence**: `protos/demo.proto` (package: `hipstershop`, no version suffix)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry is integrated with `GrpcInstrumentorClient` and `GrpcInstrumentorServer` for distributed tracing. The `OTLPSpanExporter` with `BatchSpanProcessor` exports traces to a configurable OTLP endpoint. However, tracing is conditional on `ENABLE_TRACING=1` environment variable (disabled by default in kubernetes-manifests, configurable via Helm values `googleCloudOperations.tracing`). Structured JSON logging is implemented via `logger.py` using `pythonjsonlogger` with `timestamp` and `severity` fields. However, no explicit `correlation_id`, `request_id`, or `trace_id` fields are added to log entries. Trace context propagation between logs and traces depends entirely on OTel auto-instrumentation.
- **Gap**: Tracing disabled by default. No correlation ID in structured logs. Log-to-trace correlation requires OTel auto-instrumentation (not guaranteed to inject trace ID into Python log records).
- **Compensating Controls**:
  - Enable tracing via Helm values (`googleCloudOperations.tracing: true`)
  - OTel gRPC instrumentation provides automatic trace propagation at the gRPC layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable tracing by default. Add a logging filter that injects `trace_id` and `span_id` from the OTel context into every log record. Add a `request_id` field to logs for correlation.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (OTel imports, ENABLE_TRACING check), `src/recommendationservice/logger.py` (no trace_id field), `helm-chart/values.yaml` (`googleCloudOperations.tracing: false`)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration was found in the repository. No CloudWatch/Cloud Monitoring alarms, no PagerDuty/OpsGenie integration, no SLO-based alerting. No Terraform resources for monitoring alerts. The CI/CD pipeline runs smoke tests (load generator checks for errors) but this is build-time validation, not runtime alerting.
- **Gap**: No runtime alerting on error rates or latency for the recommendation service.
- **Compensating Controls**:
  - Cloud Logging can capture error logs from stdout
  - Manual monitoring via GKE dashboard is possible but not scalable
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Cloud Monitoring alerts for: (1) gRPC error rate > 1% over 5 minutes, (2) P95 latency > 500ms, (3) pod restart count. Add alerting Terraform resources or Helm templates.
- **Evidence**: No alerting configuration found in any file. `terraform/main.tf` (no monitoring resources), `.github/workflows/ci-pr.yaml` (smoke tests only)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Infrastructure is defined as code: Terraform (`terraform/main.tf`) provisions the GKE cluster, Kubernetes manifests and Helm chart define the deployment, and Kustomize provides overlay composition. CI workflows exist for Terraform validation (`terraform-validate-ci.yaml`), Helm chart validation (`helm-chart-ci.yaml`), and Kustomize build validation (`kustomize-build-ci.yaml`). However: (1) No drift detection is configured (no AWS Config rules, no GCP Config Controller, no Terraform state drift monitoring). (2) The IaC CI pipeline validates syntax but does not perform `terraform plan` review with approval gates. (3) No CODEOWNERS file was found specifically for IaC paths.
- **Gap**: No drift detection. No Terraform plan review automation with approval gates in CI.
- **Compensating Controls**:
  - Terraform state file tracks intended state (drift detected on next apply)
  - GitHub PR reviews provide human review of IaC changes
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add drift detection (e.g., scheduled `terraform plan` in CI that alerts on drift). Add `terraform plan` output as a PR comment for review. Add CODEOWNERS for terraform/ and kubernetes-manifests/ directories.
- **Evidence**: `terraform/main.tf`, `.github/workflows/terraform-validate-ci.yaml`, `.github/workflows/helm-chart-ci.yaml`

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: The CI pipeline (`ci-pr.yaml`) runs Go unit tests for `shippingservice`, `productcatalogservice`, and `frontend/validator`, and C# unit tests for `cartservice`. No Python tests exist for the recommendation service. No API contract tests, no consumer-driven contract testing (e.g., Pact), and no proto/gRPC schema validation (e.g., `buf breaking`) in CI. Smoke tests use a load generator that exercises the full system but does not validate individual API contracts.
- **Gap**: Zero test coverage for recommendation service. No API contract testing. No proto breaking-change detection.
- **Compensating Controls**:
  - End-to-end smoke tests (load generator) provide some confidence that the service works
  - Proto file changes are visible in PRs via git diff
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add pytest-based unit tests for `recommendation_server.py`. Add gRPC API contract tests that validate request/response schemas. Integrate `buf breaking` in CI to detect proto breaking changes.
- **Evidence**: `.github/workflows/ci-pr.yaml` (no Python test step), `.github/workflows/ci-main.yaml` (no Python test step)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: Deployment is managed via Skaffold (`skaffold.yaml`), which deploys to Kubernetes. Kubernetes Deployments support rolling updates and `kubectl rollout undo` natively. Helm chart deployments support `helm rollback`. Cloud Build (`cloudbuild.yaml`) uses Skaffold for deployment. However, no explicit rollback configuration exists — no blue/green deployment, no canary deployment, no automatic rollback triggers, and no feature flags. Rollback requires manual intervention (`kubectl rollout undo` or `helm rollback`).
- **Gap**: No automated rollback. No canary or blue/green deployment. Rollback is manual.
- **Compensating Controls**:
  - Kubernetes rolling updates provide zero-downtime deployments with implicit rollback capability
  - `helm rollback` is available as a manual recovery option
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Add health-check-based automatic rollback to Kubernetes deployments (`.spec.strategy.rollingUpdate` with `maxUnavailable: 0`). Consider Flagger or Argo Rollouts for canary deployments with automatic rollback.
- **Evidence**: `skaffold.yaml`, `cloudbuild.yaml`, `kubernetes-manifests/recommendationservice.yaml` (Deployment, no rollback config)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: No test files exist for the recommendation service. No `test_recommendation_server.py`, no `*_test.py`, no pytest configuration, no Postman/Newman collections, no gRPC test client scripts (other than the manual `client.py`). The CI pipeline does not run any Python tests. `client.py` is a manual test client, not an automated test suite — it sends a single hardcoded request and prints the response.
- **Gap**: Zero automated test coverage for the recommendation service API. No input validation tests, no error handling tests, no edge case tests.
- **Compensating Controls**:
  - The end-to-end smoke test (load generator) validates that the service is reachable and returns non-error responses
  - `client.py` can be used for manual verification
- **Remediation Timeline**: 60–90 days
- **Recommendation**: Create pytest-based tests covering: (1) normal recommendation response, (2) empty cart (no filter), (3) all products in cart (empty response), (4) ProductCatalogService unavailable (error handling). Add pytest to CI pipeline for recommendation service.
- **Evidence**: No test files found in `src/recommendationservice/`. `src/recommendationservice/client.py` (manual test only). `.github/workflows/ci-pr.yaml` (no Python test step)

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a documented gRPC interface defined in `protos/demo.proto`. The `RecommendationService` defines one RPC: `ListRecommendations(ListRecommendationsRequest) returns (ListRecommendationsResponse)`. The proto file provides strongly typed message definitions with field names and types. gRPC auto-generates client/server stubs (`demo_pb2_grpc.py`). The implementation in `recommendation_server.py` directly implements the proto-defined interface. No direct database access, file-based exchange, or UI automation is required for integration.
- **Implication**: The gRPC interface is a valid, documented integration surface for agent tools. Agent tool definitions can be generated from the proto file.
- **Recommendation**: No action required. The gRPC interface satisfies the minimum viable integration surface requirement.
- **Evidence**: `protos/demo.proto` (RecommendationService definition), `src/recommendationservice/demo_pb2_grpc.py` (auto-generated stubs), `src/recommendationservice/recommendation_server.py` (ListRecommendations implementation)

### API-Q2: Machine-Readable API Specification

- **Severity**: INFO
- **Finding**: The protobuf definition in `protos/demo.proto` serves as the machine-readable API specification. It defines message types (`ListRecommendationsRequest`, `ListRecommendationsResponse`), field types, field numbers, and service RPCs. gRPC tools auto-generate client stubs from this file. The proto file is the source of truth — the generated files (`demo_pb2.py`, `demo_pb2_grpc.py`) are derived from it via `genproto.sh`. No separate OpenAPI or AsyncAPI spec exists, but for a gRPC service, the proto file is the canonical machine-readable specification.
- **Implication**: Agent frameworks that support gRPC/protobuf can auto-generate tool definitions from the proto file. Frameworks that only support REST/OpenAPI would need a gRPC-to-REST gateway (e.g., grpc-gateway, Envoy gRPC-JSON transcoding).
- **Recommendation**: If REST-based agent frameworks are targeted, add Envoy gRPC-JSON transcoding or grpc-gateway to expose the service as a REST API with an auto-generated OpenAPI spec.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/genproto.sh`, `src/recommendationservice/demo_pb2.py`, `src/recommendationservice/demo_pb2_grpc.py`

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The service only exposes one RPC: `ListRecommendations`, which is a read-only operation. No write endpoints exist. The operation is inherently idempotent — calling it multiple times with the same inputs produces the same type of output (though the specific product recommendations may vary due to random sampling). Since agent_scope is read-only, idempotency of write operations is not applicable.
- **Implication**: No idempotency concerns for the current read-only agent scope. If write operations are added in the future, idempotency must be evaluated before changing agent_scope to write-enabled.
- **Recommendation**: No action required for read-only scope.
- **Evidence**: `protos/demo.proto` (single RPC: ListRecommendations), `src/recommendationservice/recommendation_server.py` (read-only logic)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: Responses use Protocol Buffers (protobuf) binary serialization format. The `ListRecommendationsResponse` contains `repeated string product_ids`. Protobuf is strongly typed, compact, and machine-readable. gRPC tools handle serialization/deserialization automatically. While not text-based like JSON, protobuf is equally structured and has superior type safety. gRPC reflection can expose the schema at runtime.
- **Implication**: LLM-based agents that consume text (JSON) will need a translation layer (gRPC-JSON transcoding). Programmatic agent tools that use gRPC client libraries can consume protobuf natively.
- **Recommendation**: For LLM-based agents, add gRPC-JSON transcoding via Envoy to expose JSON responses. For programmatic agents, use the generated gRPC client stubs directly.
- **Evidence**: `protos/demo.proto` (protobuf message definitions), `src/recommendationservice/demo_pb2.py` (protobuf serialization)

### API-Q7: Asynchronous Operation Support

- **Severity**: INFO
- **Finding**: `ListRecommendations` is a synchronous unary-unary gRPC call. No async patterns, polling endpoints, or webhook callbacks exist. The operation fetches products from ProductCatalogService and returns a random sample — this should complete in milliseconds to low seconds, well within typical agent timeout limits. No long-running operations exist in the service.
- **Implication**: Async patterns are not needed for the current operation. If the recommendation algorithm becomes more complex (e.g., ML model inference, collaborative filtering), async patterns may become necessary.
- **Recommendation**: No action required for current functionality. Monitor latency if the recommendation algorithm is enhanced.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (synchronous ListRecommendations), `protos/demo.proto` (unary-unary RPC)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: The service does not emit events or webhooks. It is stateless — it does not maintain state that changes over time. It reads from ProductCatalogService on every request and returns a random sample. No SNS, EventBridge, SQS, Kafka, or webhook integrations were found.
- **Implication**: Event-driven agent patterns (reacting to catalog changes) would need to be built on ProductCatalogService, not the recommendation service. The recommendation service is a derived, stateless layer.
- **Recommendation**: If agents need to react to product catalog changes, implement events at the ProductCatalogService level rather than the recommendation service.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (no event emission code)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation exists. No rate limit headers (`X-RateLimit-Remaining`, `Retry-After`) are returned in gRPC metadata. The only implicit limit is the `ThreadPoolExecutor(max_workers=10)` in the gRPC server. No API Gateway throttle settings, WAF rate rules, or `aws_api_gateway_usage_plan` configurations were found.
- **Implication**: Agents have no visibility into service capacity. An agent cannot self-throttle based on rate limit headers because none are provided. This increases the risk of inadvertent overload.
- **Recommendation**: Add gRPC metadata headers communicating rate limit status. Document the service's capacity limits in the proto file comments or a service documentation file.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (max_workers=10, no rate limit headers)

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks, load test results, or APM dashboards were found. The service logic involves: (1) one gRPC call to ProductCatalogService.ListProducts, (2) list filtering and random sampling. The computational overhead of the recommendation service is minimal — latency is dominated by the ProductCatalogService call. OTel tracing (when enabled) could provide latency metrics but no dashboards or baseline metrics were found.
- **Implication**: Without latency baselines, agents cannot set appropriate timeouts. The single synchronous dependency on ProductCatalogService means recommendation latency is at least as high as catalog latency.
- **Recommendation**: Enable OTel tracing and establish P50/P95/P99 latency baselines. Set gRPC deadline in agent tool configurations based on observed P99.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (synchronous ProductCatalogService call), no benchmark files found

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: The service is stateless — it does not maintain its own state. `ListRecommendations` queries ProductCatalogService in real-time and returns a filtered, random sample. The "current state" is the live product catalog, which is accessible via the recommendation endpoint. An agent can always query current recommendations by calling ListRecommendations.
- **Implication**: The service effectively provides a real-time query interface. Since it is stateless, there is no internal state to query or inspect. Agents can treat each call as a fresh query.
- **Recommendation**: No action required. The stateless design is well-suited for agent consumption.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (ListRecommendations fetches live data on every call)

### STATE-Q3: Concurrency Controls

- **Severity**: INFO
- **Finding**: The service is stateless and read-only. No data mutation occurs, so concurrent access by multiple agent instances is inherently safe. No optimistic locking, ETags, or versioning is needed because there is no shared mutable state. The gRPC server's `ThreadPoolExecutor(max_workers=10)` handles concurrent requests independently.
- **Implication**: Multiple agents can safely call ListRecommendations concurrently without race conditions or data integrity issues.
- **Recommendation**: No action required for concurrency controls. If write operations are added in the future, implement concurrency controls before enabling multi-agent write access.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (stateless read-only logic, ThreadPoolExecutor)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: INFO
- **Finding**: The service is read-only. No data modification occurs, so the blast radius of any agent error is limited to unnecessary resource consumption (CPU, memory, network) rather than data corruption. No configurable transaction limits exist, but for a read-only service, the primary concern is resource exhaustion (addressed by STATE-Q5 rate limiting and STATE-Q7 capacity).
- **Implication**: The blast radius of a misbehaving agent is bounded to resource consumption, not data integrity. This is a favorable property for agent integration.
- **Recommendation**: No action required for transaction limits. Monitor for resource exhaustion through STATE-Q5 and STATE-Q7 mitigations.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (read-only logic)

### HITL-Q1: Draft/Pending State

- **Severity**: INFO
- **Finding**: The service has no concept of draft or pending state. It is a read-only recommendation engine that returns product suggestions. No write operations exist that would benefit from a draft-then-commit workflow. The ListRecommendations RPC returns results immediately with no commit step.
- **Implication**: Draft states are not applicable to the current service functionality. If the service evolves to support user preference settings or recommendation feedback, draft states would become relevant.
- **Recommendation**: No action required. Document that this service is read-only and does not require human-in-the-loop approval.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (read-only ListRecommendations)

### HITL-Q2: Configurable Approval Gates

- **Severity**: INFO
- **Finding**: No approval gates exist. The service performs automated recommendation retrieval only. No Step Functions, no waitForTaskToken, no approval API endpoints. Since the service is read-only, no irreversible actions can occur that would require human approval.
- **Implication**: Approval gates are not needed for a read-only recommendation service. If the service evolves to support write operations (e.g., updating user preferences), approval gates should be considered.
- **Recommendation**: No action required for current functionality.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (read-only, no approval logic)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: The CI/CD pipeline in `ci-pr.yaml` deploys PR-specific namespaces to a test GKE cluster (`prs-gke-cluster` in `us-central1`, project `online-boutique-ci`). Each PR gets an isolated namespace (`pr${PR_NUMBER}`). Skaffold (`skaffold.yaml`) supports local development with `skaffold dev`. Cloud Build (`cloudbuild.yaml`) supports deployment to any GKE cluster via substitution variables. No seed data scripts exist, but the service is stateless and depends on ProductCatalogService, which uses static product catalog data.
- **Implication**: A functional staging environment exists via the PR deployment pipeline. Agents can be tested against PR-specific deployments before production promotion.
- **Recommendation**: Document how to deploy agent test configurations to the PR staging environment. Consider adding agent-specific smoke tests to the CI pipeline.
- **Evidence**: `.github/workflows/ci-pr.yaml` (PR namespace deployment), `skaffold.yaml` (local dev support), `cloudbuild.yaml` (GKE deployment)

### DATA-Q4: System of Record Designations

- **Severity**: INFO
- **Finding**: The recommendation service is not a system of record — it derives its data from ProductCatalogService. The product catalog is the authoritative source for product data. The recommendation service has no persistent state and no master data. No system-of-record documentation was found.
- **Implication**: Agents should treat ProductCatalogService as the system of record for product data. Recommendations are derived and ephemeral.
- **Recommendation**: Document in service documentation that ProductCatalogService is the system of record. Recommendation results should not be cached as authoritative.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (fetches all data from ProductCatalogService)

### DATA-Q7: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: The log statement in `recommendation_server.py` (line 78) logs only `product_ids`: `logger.info("[Recv ListRecommendations] product_ids={}".format(prod_list))`. The `user_id` field from the request is received but NOT logged. No PII scrubbing middleware or masking library exists, but the current logging implementation does not emit PII. If additional logging is added in the future, PII could inadvertently be logged.
- **Implication**: Current logging is safe — no PII is emitted. However, the lack of a systematic PII scrubbing mechanism means future logging changes could introduce PII leakage.
- **Recommendation**: Add a PII scrubbing utility to the logging pipeline to prevent accidental PII inclusion in future log changes. Consider using a log sanitizer that redacts fields matching PII patterns.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (line 78: logs product_ids only), `src/recommendationservice/logger.py` (no PII scrubbing)

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or completeness monitoring exists. The service returns random samples from the product catalog. The "quality" of recommendations is algorithmically simple (random selection after filtering). No recommendation quality metrics (click-through rate, conversion, user satisfaction) are tracked. No data freshness SLAs are defined.
- **Implication**: The recommendation algorithm is trivial (random sampling), so data quality concerns are minimal. If the algorithm is upgraded to ML-based recommendations, data quality monitoring becomes critical.
- **Recommendation**: If the recommendation algorithm is enhanced, implement quality metrics (recommendation relevance, click-through rate, A/B test results).
- **Evidence**: `src/recommendationservice/recommendation_server.py` (random.sample — random selection algorithm)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Proto field names are human-readable and semantically meaningful: `user_id`, `product_ids`, `quantity`, `name`, `description`, `price_usd`, `categories`, `product_id`. No legacy abbreviations or encoded values requiring a data dictionary. The field names are self-documenting.
- **Implication**: LLM-based agents can reason about field meanings directly from names. No data dictionary lookup is required.
- **Recommendation**: No action required. Maintain the current naming conventions for any new proto fields.
- **Evidence**: `protos/demo.proto` (all message definitions)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog exists (no Glue Data Catalog, Collibra, Alation, DataHub). The proto file serves as the schema definition, but no broader metadata layer describes what data the system holds, what it means semantically, or how it relates to other services.
- **Implication**: Agent tool builders must read the proto file directly to understand the data model. A catalog would accelerate tool definition for teams unfamiliar with the service.
- **Recommendation**: For larger deployments, publish proto schemas to a central catalog (e.g., Buf Schema Registry) with descriptions and semantic annotations.
- **Evidence**: `protos/demo.proto` (schema only, no catalog integration)

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No formal data lineage tooling exists. The data flow is simple and traceable from code: ListRecommendations calls ProductCatalogService.ListProducts → filters out cart items → random sample → response. No ETL pipelines, no data transformations beyond in-memory filtering, no lineage documentation.
- **Implication**: The data lineage is trivially traceable from the source code. For this simple service, formal lineage tooling is not necessary. If the recommendation algorithm becomes more complex (ML model, feature store), lineage becomes important.
- **Recommendation**: Document the data flow in the service README. Consider formal lineage tooling if ML-based recommendations are introduced.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (lines 69–76: complete data flow in 8 lines)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No custom business metrics are published. No recommendation quality tracking (click-through rate, conversion rate, add-to-cart rate from recommendations). No `cloudwatch.put_metric_data` or equivalent. No custom dashboards.
- **Implication**: Without business metrics, there is no way to measure whether agent-driven recommendation consumption produces good outcomes. The current random sampling algorithm has no measurable "quality" beyond availability.
- **Recommendation**: Instrument recommendation quality metrics: recommendation-to-cart conversion rate, recommendation diversity, and recommendation latency as business KPIs.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (no metric publication code)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: INFO
- **Finding**: The recommendation service is stateless — it does not persist any data to disk, database, or cache. It reads from ProductCatalogService on every request. The Memorystore (Redis) configuration in `terraform/memorystore.tf` is for the cart service, not the recommendation service. No KMS keys, no encryption-at-rest configuration is relevant because the recommendation service has no data at rest.
- **Implication**: No encryption-at-rest concerns for this stateless service. Data-at-rest encryption should be evaluated at the ProductCatalogService level where product data is stored.
- **Recommendation**: No action required for this service. Ensure ProductCatalogService (the data source) has encryption at rest configured.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (stateless, no persistence), `terraform/memorystore.tf` (redis-cart, not for recommendation service)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: INFO
- **Finding**: Network policies are defined and discoverable. The Kustomize component `kustomize/components/network-policies/network-policy-recommendationservice.yaml` defines a NetworkPolicy that restricts ingress to only the `frontend` pod on port 8080/TCP, with unrestricted egress. The Helm chart in `helm-chart/templates/recommendationservice.yaml` includes a templated NetworkPolicy (when `networkPolicies.create=true`) with the same restrictions. An Istio AuthorizationPolicy (when `authorizationPolicies.create=true`) restricts to the frontend ServiceAccount on path `/hipstershop.RecommendationService/ListRecommendations`. CORS is not applicable (gRPC, not HTTP REST). GKE Autopilot manages underlying security groups.
- **Implication**: Network policies exist and correctly restrict access. The CI pipeline deploys with network policies enabled (`-p network-policies` in skaffold). Agent integration would require updating the NetworkPolicy to allow the agent's pod selector as an ingress source.
- **Recommendation**: When adding agent access, update the NetworkPolicy and Istio AuthorizationPolicy to include the agent's pod selector and service account. Document the network policy update process.
- **Evidence**: `kustomize/components/network-policies/network-policy-recommendationservice.yaml`, `helm-chart/templates/recommendationservice.yaml` (NetworkPolicy and AuthorizationPolicy), `helm-chart/values.yaml` (`networkPolicies.create: false` by default)

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The service exposes a documented gRPC interface defined in `protos/demo.proto` with `RecommendationService.ListRecommendations` RPC. Strongly typed protobuf messages. Auto-generated client/server stubs. No direct database access, file-based exchange, or UI automation required.
- **Gap**: N/A — passes. The gRPC interface is a documented, typed integration surface.
- **Recommendation**: No action required.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/demo_pb2_grpc.py`, `src/recommendationservice/recommendation_server.py`

#### API-Q2: Machine-Readable API Specification
- **Severity**: INFO
- **Finding**: `protos/demo.proto` serves as the machine-readable API specification. gRPC auto-generates client stubs. Proto file is the source of truth. No OpenAPI/AsyncAPI exists but is unnecessary for a gRPC service.
- **Gap**: N/A — passes. Proto file is the canonical machine-readable spec.
- **Recommendation**: If REST agent frameworks are targeted, add gRPC-JSON transcoding via Envoy.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/genproto.sh`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: No try/except in `ListRecommendations`. Unhandled exceptions propagate as gRPC `UNKNOWN`. No custom error codes, retryable booleans, or error categories.
- **Gap**: No structured error responses beyond default gRPC status codes.
- **Recommendation**: Add structured error handling with gRPC status codes and trailing metadata.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (ListRecommendations method)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Service only has a read-only RPC (ListRecommendations). No write endpoints exist. Idempotency of writes is not applicable.
- **Gap**: N/A for read-only scope.
- **Recommendation**: No action required.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: Proto package is `hipstershop` with no version suffix. No changelog. No deprecation notices.
- **Gap**: No API versioning or deprecation policy.
- **Recommendation**: Adopt `hipstershop.v1` versioning. Add `buf breaking` to CI.
- **Evidence**: `protos/demo.proto` (`package hipstershop;`)

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: Protobuf binary format — strongly typed, compact, machine-readable. gRPC handles serialization automatically.
- **Gap**: N/A — protobuf is a structured format.
- **Recommendation**: Add gRPC-JSON transcoding for LLM-based agents.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/demo_pb2.py`

#### API-Q7: Asynchronous Operation Support
- **Severity**: INFO
- **Finding**: Synchronous unary-unary gRPC call. Operation is fast (random sampling from product list). No long-running operations.
- **Gap**: No async patterns, but none are needed for the current operation.
- **Recommendation**: Monitor latency if recommendation algorithm is enhanced.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `protos/demo.proto`

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission. Service is stateless — no state changes to emit events for. No SNS/EventBridge/Kafka.
- **Gap**: No event capability, but service is stateless.
- **Recommendation**: Implement events at ProductCatalogService level if needed.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. Only implicit limit is max_workers=10 thread pool.
- **Gap**: No rate limit visibility for agents.
- **Recommendation**: Add gRPC metadata for rate limit status.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No benchmarks or latency baselines. Latency dominated by ProductCatalogService call.
- **Gap**: No latency metrics available.
- **Recommendation**: Enable OTel tracing and establish latency baselines.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: gRPC server uses `grpc.insecure_channel` and `server.add_insecure_port`. No TLS, mTLS, OAuth2, API key, or service account authentication. No audit log attribution for agent identity.
- **Gap**: No application-level machine identity authentication.
- **Recommendation**: Introduce mTLS via Istio or application-level JWT authentication.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `kubernetes-manifests/recommendationservice.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No application-level permission model. Istio AuthorizationPolicy provides network-level restriction when enabled. All authenticated callers have identical access.
- **Gap**: No scoped permissions at the application layer.
- **Recommendation**: Implement gRPC interceptors for permission checks. Enable Istio AuthorizationPolicy.
- **Evidence**: `kubernetes-manifests/recommendationservice.yaml`, `helm-chart/templates/recommendationservice.yaml`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: Single RPC with no permission checks. Istio AuthorizationPolicy restricts to specific operation path when enabled but is disabled by default.
- **Gap**: No application-level action-level authorization.
- **Recommendation**: Enable Istio AuthorizationPolicies in production.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: `user_id` in request is an opaque, unverified string. No JWT parsing, no OAuth2 on-behalf-of flow.
- **Gap**: No verified identity propagation.
- **Recommendation**: Implement JWT-based identity propagation.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between agent access modes. Single auth path (none). No audit differentiation.
- **Gap**: Cannot differentiate agent-as-self from agent-on-behalf-of-user.
- **Recommendation**: Define separate ServiceAccounts for different agent modes.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `protos/demo.proto`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: No secrets management. No hardcoded credentials found. gRPC channel is insecure. Environment variables contain non-secret configuration only.
- **Gap**: No secrets management infrastructure for when credentials are introduced.
- **Recommendation**: Deploy External Secrets Operator with GCP Secret Manager.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `kubernetes-manifests/recommendationservice.yaml`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured JSON logging via pythonjsonlogger. Logs product_ids but not authenticated principals. No immutable log storage. No CloudTrail equivalent.
- **Gap**: No principal identity in logs. No immutable storage.
- **Recommendation**: Add caller identity to logs. Configure immutable log storage.
- **Evidence**: `src/recommendationservice/logger.py`, `src/recommendationservice/recommendation_server.py`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No mechanism to suspend individual agent identities without cluster-level changes.
- **Gap**: No application-level agent suspension.
- **Recommendation**: Implement API key-based auth with revocation capability.
- **Evidence**: `helm-chart/templates/recommendationservice.yaml`, `helm-chart/values.yaml`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Stateless, read-only service. No multi-step write operations. No compensation needed for current functionality.
- **Gap**: No compensation mechanism (not needed for current read-only service).
- **Recommendation**: Implement compensation patterns if write operations are added.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Stateless service queries ProductCatalogService in real-time. Each ListRecommendations call returns current data.
- **Gap**: N/A — service provides real-time query interface.
- **Recommendation**: No action required.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### STATE-Q3: Concurrency Controls
- **Severity**: INFO
- **Finding**: Stateless read-only service. No shared mutable state. Concurrent reads are inherently safe.
- **Gap**: N/A — no concurrency concerns for read-only service.
- **Recommendation**: Implement concurrency controls if write operations are added.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breaker, retry, or timeout on ProductCatalogService gRPC channel. Downstream failures cascade directly.
- **Gap**: No resilience patterns on external dependency.
- **Recommendation**: Add gRPC timeout options, retry with exponential backoff, and circuit breaker pattern.
- **Evidence**: `src/recommendationservice/recommendation_server.py` (line 99: `grpc.insecure_channel`)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting. Only implicit limit is max_workers=10 thread pool.
- **Gap**: No rate limiting to prevent agent-driven overload.
- **Recommendation**: Add gRPC server interceptors for rate limiting.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `kubernetes-manifests/recommendationservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: INFO
- **Finding**: Read-only service. Blast radius limited to resource consumption, not data corruption.
- **Gap**: No transaction limits, but not needed for read-only service.
- **Recommendation**: Monitor resource consumption via STATE-Q5 and STATE-Q7 mitigations.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: Single replica, no HPA, max_workers=10, no load tests. Resource limits: 200m CPU / 450Mi memory.
- **Gap**: Not sized or tested for agent traffic patterns.
- **Recommendation**: Add HPA, increase max_workers, conduct load testing.
- **Evidence**: `kubernetes-manifests/recommendationservice.yaml`, `src/recommendationservice/recommendation_server.py`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: INFO
- **Finding**: No draft/pending state. Read-only service with no write operations that would benefit from draft states.
- **Gap**: N/A for read-only service.
- **Recommendation**: No action required.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: INFO
- **Finding**: No approval gates. Read-only service with no irreversible actions.
- **Gap**: N/A for read-only service.
- **Recommendation**: No action required.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: INFO
- **Finding**: PR-specific namespace deployment to test GKE cluster exists. Skaffold supports local dev. Service is stateless with static product data.
- **Gap**: No agent-specific test configurations.
- **Recommendation**: Add agent-specific smoke tests to CI pipeline.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `skaffold.yaml`, `cloudbuild.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: BLOCKER
- **Finding**: `user_id` field in proto is unclassified PII. No data classification tags, field-level encryption, or PII detection. `user_id` is received but unused by recommendation logic.
- **Gap**: No data classification at field level. `user_id` unprotected.
- **Recommendation**: Classify data fields. Mark `user_id` as PII. Consider removing unused `user_id`.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/recommendation_server.py`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Deployment defaults to us-central1. No data residency requirements documented. No cross-region controls.
- **Gap**: No data residency configuration.
- **Recommendation**: Document residency requirements. Control cross-region data transmission.
- **Evidence**: `terraform/variables.tf`, `protos/demo.proto`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: Hardcoded max_responses=5. No pagination, sorting, or configurable limit.
- **Gap**: No configurable query parameters.
- **Recommendation**: Add `max_results` field to proto request.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `protos/demo.proto`

#### DATA-Q4: System of Record Designations
- **Severity**: INFO
- **Finding**: Service is not a system of record — derives data from ProductCatalogService. No SoR documentation.
- **Gap**: No SoR documentation.
- **Recommendation**: Document ProductCatalogService as the system of record.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamps in `ListRecommendationsResponse`. Response contains only product_ids.
- **Gap**: No temporal data in API responses.
- **Recommendation**: Add timestamp field to response proto.
- **Evidence**: `protos/demo.proto`, `src/recommendationservice/logger.py`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No freshness signaling. Service fetches live data but does not communicate this.
- **Gap**: No freshness indicators in responses.
- **Recommendation**: Add gRPC response metadata for data freshness.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: user_id is NOT logged — only product_ids are logged. Current logging is PII-safe. No systematic PII scrubbing mechanism.
- **Gap**: No PII scrubbing framework for future changes.
- **Recommendation**: Add PII scrubbing utility to logging pipeline.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `src/recommendationservice/logger.py`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics. Random sampling algorithm with no quality measurement.
- **Gap**: No quality metrics.
- **Recommendation**: Implement quality metrics if algorithm is enhanced.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Proto schema defines all types and RPCs. Version-controlled in git. No version suffix in package. No schema registry.
- **Gap**: No schema versioning beyond git. No breaking-change detection.
- **Recommendation**: Add proto versioning. Integrate `buf` for breaking-change detection.
- **Evidence**: `protos/demo.proto`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are human-readable: user_id, product_ids, name, description, price_usd, categories. No legacy abbreviations.
- **Gap**: N/A — field names are self-documenting.
- **Recommendation**: Maintain current naming conventions.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. Proto file serves as schema definition only.
- **Gap**: No broader metadata layer.
- **Recommendation**: Publish proto to central schema registry for larger deployments.
- **Evidence**: `protos/demo.proto`

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No formal lineage tooling. Data flow is trivially traceable: ProductCatalogService → filter → random sample → response.
- **Gap**: No formal lineage (not needed for this simple service).
- **Recommendation**: Document data flow in README.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OTel integrated but tracing disabled by default. Structured JSON logging via pythonjsonlogger. No correlation_id or trace_id in log entries.
- **Gap**: Tracing disabled by default. No log-to-trace correlation.
- **Recommendation**: Enable tracing by default. Add trace_id to log records.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `src/recommendationservice/logger.py`, `helm-chart/values.yaml`

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. No Cloud Monitoring alarms. No PagerDuty/OpsGenie.
- **Gap**: No runtime alerting.
- **Recommendation**: Configure Cloud Monitoring alerts for error rates and latency.
- **Evidence**: No alerting config found. `terraform/main.tf`, `.github/workflows/ci-pr.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. No recommendation quality tracking.
- **Gap**: No business outcome measurement.
- **Recommendation**: Instrument recommendation quality metrics.
- **Evidence**: `src/recommendationservice/recommendation_server.py`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: IaC exists (Terraform, K8s manifests, Helm, Kustomize). CI validation for Terraform, Helm, Kustomize. No drift detection. No Terraform plan review automation.
- **Gap**: No drift detection. No Terraform plan approval gates.
- **Recommendation**: Add drift detection and Terraform plan review in CI.
- **Evidence**: `terraform/main.tf`, `.github/workflows/terraform-validate-ci.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI runs Go and C# tests only. Zero Python tests. No API contract tests. No proto breaking-change detection.
- **Gap**: No test coverage for recommendation service. No contract testing.
- **Recommendation**: Add pytest tests. Integrate `buf breaking` in CI.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `.github/workflows/ci-main.yaml`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Skaffold and Kubernetes rolling updates. No automated rollback. No canary/blue-green. Manual rollback via kubectl or helm.
- **Gap**: No automated rollback.
- **Recommendation**: Add health-check-based automatic rollback. Consider Flagger/Argo Rollouts.
- **Evidence**: `skaffold.yaml`, `cloudbuild.yaml`, `kubernetes-manifests/recommendationservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: Zero automated test coverage. No pytest, no test files. `client.py` is a manual test only.
- **Gap**: Zero test coverage for recommendation service API.
- **Recommendation**: Create pytest tests. Add to CI pipeline.
- **Evidence**: `src/recommendationservice/client.py`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: INFO
- **Finding**: Stateless service with no data at rest. No persistence to disk or database. Memorystore config is for cart service.
- **Gap**: N/A — no data at rest to encrypt.
- **Recommendation**: Ensure ProductCatalogService has encryption at rest.
- **Evidence**: `src/recommendationservice/recommendation_server.py`, `terraform/memorystore.tf`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: INFO
- **Finding**: NetworkPolicy restricts ingress to frontend on port 8080. Istio AuthorizationPolicy restricts to frontend ServiceAccount. Kustomize and Helm both define network policies. CORS N/A for gRPC.
- **Gap**: N/A — network policies exist and are discoverable.
- **Recommendation**: Update NetworkPolicy to include agent pod selector when enabling agent access.
- **Evidence**: `kustomize/components/network-policies/network-policy-recommendationservice.yaml`, `helm-chart/templates/recommendationservice.yaml`

## Evidence Index

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q6, API-Q7, AUTH-Q4, AUTH-Q5, DATA-Q1, DATA-Q2, DATA-Q3, DATA-Q5, DISC-Q1, DISC-Q2 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `src/recommendationservice/recommendation_server.py` | API-Q1, API-Q3, API-Q4, API-Q7, API-Q8, API-Q9, API-Q10, AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q7, STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, STATE-Q7, HITL-Q1, HITL-Q2, DATA-Q1, DATA-Q3, DATA-Q4, DATA-Q6, DATA-Q7, DATA-Q8, DISC-Q4, OBS-Q1, OBS-Q3, ENG-Q5 |
| `src/recommendationservice/logger.py` | AUTH-Q7, DATA-Q5, DATA-Q7, OBS-Q1 |
| `src/recommendationservice/client.py` | ENG-Q4 |
| `src/recommendationservice/demo_pb2_grpc.py` | API-Q1, API-Q3 |
| `src/recommendationservice/demo_pb2.py` | API-Q2, API-Q6 |
| `src/recommendationservice/genproto.sh` | API-Q2 |

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/main.tf` | ENG-Q1, OBS-Q2 |
| `terraform/variables.tf` | DATA-Q2 |
| `terraform/memorystore.tf` | ENG-Q5 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `src/recommendationservice/Dockerfile` | (Referenced for file inventory — multi-stage Python 3.14 Alpine build) |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `src/recommendationservice/requirements.txt` | OBS-Q1 (OTel dependencies) |
| `src/recommendationservice/requirements.in` | OBS-Q1 (direct dependencies) |

### Kubernetes Manifests
| File | Questions Referenced |
|------|---------------------|
| `kubernetes-manifests/recommendationservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q6, STATE-Q5, STATE-Q7, ENG-Q3, ENG-Q6 |
| `helm-chart/templates/recommendationservice.yaml` | AUTH-Q2, AUTH-Q3, AUTH-Q8, ENG-Q6 |
| `helm-chart/values.yaml` | AUTH-Q3, AUTH-Q8, OBS-Q1 |
| `kustomize/components/network-policies/network-policy-recommendationservice.yaml` | ENG-Q6 |
| `istio-manifests/frontend-gateway.yaml` | (Referenced for file inventory — Istio gateway config) |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | HITL-Q3, OBS-Q2, ENG-Q2, ENG-Q4 |
| `.github/workflows/ci-main.yaml` | ENG-Q2 |
| `.github/workflows/terraform-validate-ci.yaml` | ENG-Q1 |
| `.github/workflows/helm-chart-ci.yaml` | ENG-Q1 |
| `cloudbuild.yaml` | HITL-Q3, ENG-Q3 |
| `skaffold.yaml` | HITL-Q3, ENG-Q3 |

---

*End of Agentic Readiness Assessment Report*
