# Agentic Readiness Analysis Report

**Target**: ./services/microservices-demo/src/productcatalogservice
**Date**: 2026-04-16
**Analyzed by**: AWS Transform Custom — Agentic Readiness Analysis
**Repository Type**: application
**Service Archetype**: stateless-utility (auto-detected)
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, grpc, catalog
**Context**: Go gRPC service serving product catalog from a JSON file.

**Archetype Justification**: No database writes, no user-specific state, no message queues. All three RPCs (ListProducts, GetProduct, SearchProducts) are read-only. Data is served from a static JSON file or read-only AlloyDB queries. Product catalog is public reference data.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 1 | **RISKs**: 12 | **INFOs**: 18

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

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
**Extended Questions Triggered**: 7 (all INFO)
**Extended Questions Not Triggered**: 12
**Questions N/A (repo_type: application)**: 0
**Service Archetype**: stateless-utility (auto-detected)

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server in `server.go` creates a plain `grpc.NewServer(grpc.StatsHandler(otelgrpc.NewServerHandler()))` with no authentication interceptors, no TLS, and no mTLS. Outbound connections use `insecure.NewCredentials()` in `mustConnGRPC`. The Helm chart has `authorizationPolicies.create: false`, so no Istio AuthorizationPolicy is deployed. Any client that can reach port 3550 can call all RPCs without authentication.
- **Gap**: No machine identity authentication mechanism exists. The service cannot distinguish which agent (or any caller) made a request. No authenticated principal for audit attribution.
- **Remediation**:
  - **Immediate**: Enable `authorizationPolicies.create: true` in the Helm values to deploy Istio AuthorizationPolicies restricting callers by service account identity. Add gRPC server-side TLS via a unary interceptor that validates bearer tokens (JWT) or mTLS client certificates.
  - **Target State**: All inbound gRPC calls are authenticated via mTLS or OAuth2 client credentials. Each agent has a unique service account identity. Authenticated principal is logged with every request.
  - **Estimated Effort**: Medium
  - **Dependencies**: AUTH-Q5 (credential management for TLS certificates), AUTH-Q6 (audit logging must capture the machine identity principal).
- **Evidence**: `server.go` (`grpc.NewServer(...)`, `insecure.NewCredentials()`), `product_catalog.go` (no auth checks in RPCs), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The service API is defined via Protocol Buffers (`demo.proto`), and generated Go stubs exist in `genproto/demo_grpc.pb.go` and `genproto/demo.pb.go`. However, the source `.proto` file is not in this service directory — it is referenced at `../../protos/demo.proto` per `genproto.sh`. The generated code is present and versioned, but the canonical specification lives externally.
- **Gap**: The machine-readable API specification (`.proto` file) is not co-located with the service code. No mechanism to verify that generated stubs are current with the source proto definition.
- **Compensating Controls**:
  - Use the generated `genproto/demo_grpc.pb.go` as the de facto spec for agent tool definition — it contains complete method signatures and message types.
  - Add gRPC reflection to the server (`reflection.Register(srv)`) to allow runtime schema discovery.
- **Remediation Timeline**: 30 days
- **Recommendation**: Copy or symlink the `.proto` file into this repository, or add a CI step that validates generated code matches the source proto.
- **Evidence**: `genproto.sh` (references `../../protos/demo.proto`), `genproto/demo_grpc.pb.go`, `genproto/demo.pb.go`

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The service uses gRPC status codes for error responses. `product_catalog.go` returns `status.Errorf(codes.NotFound, "no product with ID %s", req.Id)` for missing products and `status.Errorf(codes.Unimplemented, ...)` for the Watch health check. These are structured (code + message), but limited to only two error types. Catalog load failures in `parseCatalog` silently return an empty product list rather than propagating a structured error to the caller.
- **Gap**: No rich error details (retryable boolean, error category, structured error body). Only `NotFound` and `Unimplemented` status codes are used. Catalog load failures are swallowed silently.
- **Compensating Controls**:
  - Map gRPC status codes to agent retry logic: `UNAVAILABLE` and `DEADLINE_EXCEEDED` → retryable; `NOT_FOUND`, `INVALID_ARGUMENT` → terminal.
  - Use gRPC error details proto (`google.rpc.Status` with `details` field) to add structured metadata.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Implement gRPC rich error model using `errdetails` package. Propagate catalog load errors as `codes.Internal` instead of returning empty results.
- **Evidence**: `product_catalog.go` (`status.Errorf(codes.NotFound, ...)`, `parseCatalog` returns `[]*pb.Product{}` on error)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No authorization model exists in the application code. All three RPCs are fully open to any caller. The Helm chart defines an AuthorizationPolicy template restricting callers to frontend, checkoutservice, and recommendationservice by service account — but `authorizationPolicies.create` is `false`, so this policy is not deployed.
- **Gap**: No scoped permissions enforced. An agent identity cannot be granted read-only access to specific products without inheriting access to the entire catalog.
- **Compensating Controls**:
  - Enable `authorizationPolicies.create: true` in Helm values to deploy the Istio AuthorizationPolicy.
  - Limit network access via NetworkPolicy (already defined in Helm when `networkPolicies.create: true`).
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable the existing Istio AuthorizationPolicy in Helm values. Add agent service accounts to the allowed principals list.
- **Evidence**: `product_catalog.go` (no permission checks), `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy template exists but gated), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No action-level authorization exists. All three RPCs are accessible without permission differentiation. The Helm AuthorizationPolicy template (when enabled) restricts to specific paths (`/hipstershop.ProductCatalogService/GetProduct`, `/hipstershop.ProductCatalogService/ListProducts`) but does not include `SearchProducts` — indicating incomplete method-level coverage.
- **Gap**: Cannot restrict an agent to only `GetProduct` while denying `ListProducts` or `SearchProducts`. The AuthorizationPolicy template is incomplete (missing SearchProducts path).
- **Compensating Controls**:
  - Enable and complete the Istio AuthorizationPolicy to cover all three RPC paths.
  - Implement per-method authorization in a gRPC interceptor.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Update the Helm AuthorizationPolicy template to include all three RPC paths. Enable `authorizationPolicies.create: true`.
- **Evidence**: `product_catalog.go` (no permission checks), `helm-chart/templates/productcatalogservice.yaml` (AuthorizationPolicy missing `/hipstershop.ProductCatalogService/SearchProducts`)

### AUTH-Q5: Credential Management

- **Severity**: RISK
- **Finding**: Mixed credential management practices. **Positive**: `catalog_loader.go` uses Google Cloud Secret Manager (`getSecretPayload` function) to retrieve the AlloyDB password. **Negative**: The gRPC server uses `insecure.NewCredentials()` for outbound connections. No TLS certificates are managed. No hardcoded credentials found in code or configuration files.
- **Gap**: No TLS certificate management for the gRPC server. Outbound connections use insecure transport.
- **Compensating Controls**:
  - Restrict network access at the infrastructure layer (Kubernetes NetworkPolicy) to compensate for insecure transport.
  - Extend Secret Manager usage to manage TLS certificates.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable TLS on the gRPC server using certificates managed through Secret Manager or a certificate authority. Replace `insecure.NewCredentials()` with TLS credentials.
- **Evidence**: `catalog_loader.go` (`getSecretPayload` function), `server.go` (`insecure.NewCredentials()`)

### AUTH-Q6: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured JSON logging is implemented via logrus with JSONFormatter (`server.go` init function), outputting timestamp, severity, and message fields. However, no authenticated principal is logged because no authentication exists (AUTH-Q1). No CloudTrail configuration, no immutable log storage, no S3 bucket with object lock.
- **Gap**: Logs do not capture who made each request. No immutable or tamper-evident log storage configuration.
- **Compensating Controls**:
  - Route container stdout logs to a centralized, append-only log system (CloudWatch Logs with retention policies).
  - Add request-level metadata (caller identity, trace ID) once AUTH-Q1 is resolved.
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1)
- **Recommendation**: After implementing authentication (AUTH-Q1), add a gRPC interceptor that logs the authenticated principal for every request. Configure immutable log storage.
- **Evidence**: `server.go` (logrus JSONFormatter with timestamp, severity, message — no principal field)

### AUTH-Q7: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity suspension mechanism exists. No API key revocation, no IAM role deactivation, no service account disable. Since no authentication exists (AUTH-Q1), there is no identity to suspend.
- **Gap**: Cannot isolate or revoke a misbehaving agent's access without taking down the entire service or blocking at the network layer.
- **Compensating Controls**:
  - Block specific agent IP addresses or pods at the network layer (Kubernetes NetworkPolicy) as an emergency measure.
  - Once AUTH-Q1 is implemented, design the identity system with per-agent revocation capability.
- **Remediation Timeline**: 60–90 days (dependent on AUTH-Q1)
- **Recommendation**: When implementing AUTH-Q1, ensure each agent has a unique identity that can be individually revoked.
- **Evidence**: `server.go` (no auth model, no revocation mechanism)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway throttling configuration, no WAF rate rules, no application-level rate limiting middleware. The gRPC server accepts unlimited concurrent connections on port 3550.
- **Gap**: A runaway agent loop could overwhelm the service with requests at machine speed. No protection against accidental or malicious request floods.
- **Compensating Controls**:
  - Deploy the service behind an API Gateway or load balancer with rate limiting configured.
  - Use gRPC server options (`grpc.MaxConcurrentStreams()`) to limit concurrency.
- **Remediation Timeline**: 30 days
- **Recommendation**: Add gRPC server-side rate limiting via an interceptor or deploy behind an API Gateway with usage plans and throttling.
- **Evidence**: `server.go` (`grpc.NewServer()` with no rate limiting options)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry tracing is implemented in `server.go` via `initTracing()` with OTLP gRPC exporter and trace context propagation (TraceContext + Baggage). The gRPC server uses `otelgrpc.NewServerHandler()` for automatic span creation. However, tracing is gated behind `ENABLE_TRACING=1` environment variable, and the Helm chart has `googleCloudOperations.tracing: false`, so `ENABLE_TRACING` is not set in the deployment — tracing is disabled by default. Structured JSON logging via logrus is configured with `timestamp`, `severity`, and `message` fields. No correlation between logs and traces — no `trace_id` or `request_id` field in log entries.
- **Gap**: Tracing is disabled by default in the Helm deployment. Logs and traces are not correlated.
- **Compensating Controls**:
  - Set `googleCloudOperations.tracing: true` in Helm values to enable tracing.
  - Add OpenTelemetry log bridge to inject trace context into logrus entries.
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable tracing by default in Helm values. Add trace ID injection into logrus log entries.
- **Evidence**: `server.go` (`ENABLE_TRACING`, `initTracing()`, `otelgrpc.NewServerHandler()`, logrus JSONFormatter), `helm-chart/values.yaml` (`tracing: false`), `go.mod` (OpenTelemetry dependencies)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration found in the repository. No CloudWatch alarms, no Prometheus alerting rules, no PagerDuty/OpsGenie integration. No SLO-based alerting.
- **Gap**: API degradation (elevated error rates, increased latency) will not generate alerts. Agents consuming the service will be the first to discover problems.
- **Compensating Controls**:
  - If deployed on GKE with Cloud Monitoring, leverage platform-level alerting.
  - Define alerting rules externally in the deployment infrastructure.
- **Remediation Timeline**: 30 days
- **Recommendation**: Configure alerting on gRPC error rates (by status code) and P95 latency. Integrate with an incident management system.
- **Evidence**: No alerting configuration files found. `server.go` (no alerting setup), `go.mod` (no alerting libraries)

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: The Helm chart (`helm-chart/templates/productcatalogservice.yaml`) defines Kubernetes Deployment, Service, NetworkPolicy, Istio Sidecar, and AuthorizationPolicy resources — providing IaC for the deployment surface. However, AuthorizationPolicies are disabled (`authorizationPolicies.create: false`), leaving the security surface ungoverned. No drift detection configuration exists. The Helm chart is in a parent repository directory, not co-located with the service source code.
- **Gap**: IaC exists in the Helm chart but the security surface is ungoverned (AuthorizationPolicies disabled). No drift detection.
- **Compensating Controls**:
  - The Helm chart provides peer-reviewable IaC for the Kubernetes deployment surface.
  - Enable AuthorizationPolicies to govern the security surface.
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Enable `authorizationPolicies.create: true`. Add drift detection for Kubernetes resources.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml` (Deployment, Service, NetworkPolicy, AuthorizationPolicy), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: No CI/CD pipeline configuration found in the service directory. The parent repository has `cloudbuild.yaml` and `.github/workflows/` but no protobuf breaking change detection (e.g., `buf breaking`). No API contract testing.
- **Gap**: No automated pipeline with contract testing to detect API-breaking changes before they reach production and break agents.
- **Compensating Controls**:
  - CI/CD may be defined in the parent repository's `cloudbuild.yaml`.
  - Run `buf breaking` locally before committing proto changes.
- **Remediation Timeline**: 60 days
- **Recommendation**: Add protobuf breaking change detection (`buf breaking`) to the CI pipeline. Add contract tests verifying gRPC service behavior.
- **Evidence**: No CI/CD configuration in service directory. `cloudbuild.yaml` (parent repo — no contract testing)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a well-defined gRPC interface via Protocol Buffers. `genproto/demo_grpc.pb.go` defines `ProductCatalogService` with three RPCs: `ListProducts`, `GetProduct`, and `SearchProducts`. This is a strongly-typed, documented API with auto-generated client stubs. gRPC with protobuf qualifies as a documented API interface.
- **Implication**: Agent tool definitions can be generated directly from the protobuf service definition. gRPC's strong typing reduces integration errors. However, gRPC requires specific client libraries, which may limit which agent frameworks can consume it directly.
- **Recommendation**: Consider adding a gRPC-Gateway or Envoy JSON transcoding proxy to expose the service as REST/JSON for agent frameworks that don't support native gRPC.
- **Evidence**: `genproto/demo_grpc.pb.go` (`ProductCatalogServiceServer` interface), `product_catalog.go` (implementation)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: The service has no write operations. All three RPCs (ListProducts, GetProduct, SearchProducts) are read-only. Idempotency is inherently satisfied — read operations are naturally idempotent.
- **Implication**: No idempotency concerns for read-only agent scope. If write operations are added in the future, idempotency keys must be implemented.
- **Recommendation**: No action needed for current scope.
- **Evidence**: `product_catalog.go` (all RPCs are read-only)

### API-Q5: Structured Response Format

- **Severity**: INFO
- **Finding**: Response format is Protocol Buffers binary over gRPC (HTTP/2). Responses are strongly typed with well-defined message structures: `ListProductsResponse` (array of `Product`), `Product` (id, name, description, picture, priceUsd as `Money`, categories), `SearchProductsResponse` (array of `Product`).
- **Implication**: Protobuf is a highly structured, efficient format. Agent tooling will need a protobuf deserializer. The binary format is not directly human-readable but is more compact and type-safe than JSON.
- **Recommendation**: If human-readable responses are needed for debugging, add gRPC reflection or a JSON transcoding proxy.
- **Evidence**: `genproto/demo.pb.go` (message type definitions), `products.json` (JSON representation of the data model)

### API-Q8: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation. No rate limit headers returned in gRPC responses. No `X-RateLimit-Remaining` or `Retry-After` equivalent in gRPC metadata.
- **Implication**: Agents have no signal to self-throttle. Without rate limit awareness, agents will call endpoints at maximum speed.
- **Recommendation**: When implementing rate limiting (STATE-Q5), also expose rate limit status via gRPC trailing metadata so agents can self-throttle.
- **Evidence**: `server.go` (no rate limit metadata), `product_catalog.go` (no rate limit headers)

### AUTH-Q4: Identity Propagation and Delegation

- **Severity**: INFO
- **Finding**: No identity propagation mechanism exists. No JWT parsing middleware, no OAuth2 on-behalf-of flows, no user context headers. The gRPC context does not extract or propagate any user identity. No distinction between agent-as-self and agent-on-behalf-of-user. Archetype calibration: stateless-utility serving public data — downgraded to INFO per TD.
- **Implication**: For a read-only product catalog serving public data, identity propagation is low impact — all products are returned regardless of caller identity.
- **Recommendation**: Implement identity propagation via gRPC metadata headers when user-specific filtering is needed in the future.
- **Evidence**: `product_catalog.go` (context not inspected for identity), `server.go` (no metadata interceptors)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or rollback logic exists. The service has no write operations — all three RPCs are read-only. Read operations are inherently safe and require no rollback.
- **Implication**: For read-only agent scope, compensation is not applicable. If agent scope expands to write-enabled, this becomes a BLOCKER.
- **Recommendation**: No action needed for current scope.
- **Evidence**: `product_catalog.go` (all RPCs are read-only)

### STATE-Q6: Blast Radius and Transaction Limits ⚡

- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No configurable transaction limits. The service has no write operations, so there are no records to modify, no spend to limit, and no delete operations to constrain.
- **Implication**: For read-only agent scope, blast radius controls are not applicable. If scope expands to write-enabled, transaction limits must be implemented.
- **Recommendation**: No action needed for current scope.
- **Evidence**: `product_catalog.go` (all RPCs are read-only)

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: The product catalog data (`products.json`) contains only public product information: id, name, description, picture path, price (USD), and categories. No PII, PHI, financial records (beyond product prices), or credentials are present. The AlloyDB table schema queries the same fields. The proto file includes a `Data Classification: PUBLIC` comment for the ProductCatalogService section. For a stateless-utility serving public reference data, the absence of formal field-level classification tags is low risk.
- **Implication**: The data is inherently non-sensitive (public product catalog). No immediate regulatory exposure. Classification gap does not gate agent deployment.
- **Recommendation**: Formally classify the product catalog data as "Public" and implement a data classification policy that triggers review when new fields are added.
- **Evidence**: `products.json` (9 products with public fields only), `catalog_loader.go` (AlloyDB query selecting same public fields), `protos/demo.proto` (`Data Classification: PUBLIC` comment)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No data residency or sovereignty configuration found. The AlloyDB connection parameters are configured via environment variables (`PROJECT_ID`, `REGION`) but no explicit residency constraints are defined. The product catalog data does not contain regulated personal data. For a read-only agent scope with public data, residency is informational only.
- **Implication**: Product catalog data is non-regulated — no immediate residency risk for read-only agent access.
- **Recommendation**: Document data residency requirements as part of the data classification effort (DATA-Q1).
- **Evidence**: `catalog_loader.go` (env vars: `PROJECT_ID`, `REGION`), `products.json` (non-regulated product data)

### DATA-Q6: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: No PII redaction middleware or log scrubbing found. Structured JSON logging is configured (logrus JSONFormatter) but no filters or masking patterns are applied. However, the product catalog data contains no PII — only product IDs, names, descriptions, pictures, prices, and categories. For a stateless-utility serving public data with no PII, the absence of log scrubbing is low risk.
- **Implication**: Current data contains no PII, so the immediate risk is negligible. If PII-containing data is ever added to the service, it would flow into logs unredacted.
- **Recommendation**: Add a logrus hook for PII pattern redaction as a preventive control before expanding data scope.
- **Evidence**: `server.go` (logrus JSONFormatter — no scrubbing), `products.json` (no PII fields)

### DATA-Q7: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling reports, completeness metrics, or freshness SLAs. `products.json` contains 9 products with complete data (all fields populated). No null values, no duplicate detection, no data quality dashboards.
- **Implication**: Current data appears complete (small, manually curated dataset). As the catalog grows (especially via AlloyDB), data quality monitoring becomes important.
- **Recommendation**: Implement data completeness checks for the AlloyDB catalog path.
- **Evidence**: `products.json` (9 products, all fields populated)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names are semantically meaningful and human-readable. Product fields: `id`, `name`, `description`, `picture`, `price_usd` (with `currency_code`, `units`, `nanos`), `categories`. Request fields: `Id` (GetProductRequest), `Query` (SearchProductsRequest). No legacy abbreviations or cryptic codes.
- **Implication**: Agent LLMs can reason about field semantics directly from field names. No data dictionary lookup needed.
- **Recommendation**: Maintain this naming convention. Document `nanos` semantics (fractional currency units in 1/1,000,000,000).
- **Evidence**: `genproto/demo.pb.go` (Product message fields), `products.json` (field names)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No data catalog or metadata layer. No AWS Glue Data Catalog, no Collibra, no Alation, no DataHub references. No metadata files describing the product catalog schema semantics.
- **Implication**: Agent tool builders must examine the protobuf definition and source code to understand what data the service holds. Manageable for a small, focused service.
- **Recommendation**: Add a brief data dictionary to the README or a separate SCHEMA.md documenting field meanings, valid values, and data sources.
- **Evidence**: `README.md` (no data dictionary), no metadata files found

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics. No custom CloudWatch metrics, no business KPI dashboards, no metrics tracking catalog query patterns, search effectiveness, or product view frequency.
- **Implication**: When agents consume the catalog service, there is no signal for whether agent interactions produce good outcomes (e.g., are agents finding relevant products, are search queries effective).
- **Recommendation**: Add custom metrics for business-relevant signals: search-hit-rate, products-viewed-per-session, empty-search-result-rate.
- **Evidence**: `server.go` (no custom metrics), `product_catalog.go` (no metrics instrumentation)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: INFO
- **Finding**: No sandbox or staging environment configuration found. The Dockerfile defines a single build target with no environment-specific variants. No docker-compose for local testing. No environment-specific configuration files. `products.json` serves as both development and production data. For a stateless-utility serving static data from a JSON file, local testing is straightforward — run the binary with `products.json` in the working directory.
- **Implication**: No dedicated staging environment, but the stateless nature and static data source make local testing practical. The first time an agent bug is discovered could still be in production if no staging instance is deployed.
- **Recommendation**: Create a docker-compose.yml for local development/testing. Deploy a separate instance for staging.
- **Evidence**: `Dockerfile` (single build target), `products.json` (single data file, no environment variants)

### DISC-Q1: Schema Versioning and API Contracts

- **Severity**: INFO
- **Finding**: Schemas are defined via Protocol Buffers. The generated Go code is versioned in the repository. The gRPC service is registered under `hipstershop.ProductCatalogService` with no version prefix (e.g., no `hipstershop.v1.ProductCatalogService`). The source `.proto` file lives outside this service at `../../protos/demo.proto`. No schema registry. No database migration files for AlloyDB. No breaking change detection in CI. For a stateless-utility with a small, stable API surface (3 read-only RPCs), the practical risk of unversioned schemas is lower than for services with evolving write APIs.
- **Implication**: Breaking protobuf changes would silently break agent tool schemas, but the API surface is small and stable. Protobuf's built-in field numbering provides implicit backward compatibility.
- **Recommendation**: Adopt protobuf package versioning (e.g., `hipstershop.productcatalog.v1`). Include the `.proto` file in this repository. Add `buf breaking` to CI.
- **Evidence**: `genproto/demo_grpc.pb.go` (`ServiceName: "hipstershop.ProductCatalogService"` — no version prefix), `genproto.sh` (`protodir=../../protos`)

### ENG-Q3: Rollback Capability

- **Severity**: INFO
- **Finding**: No rollback configuration in this repository. No blue/green deployment, no CodeDeploy, no Helm rollback configuration, no feature flags. The Dockerfile uses a pinned base image hash, enabling deterministic rebuilds. For a stateless-utility with no persistent state, rollback risk is limited to API contract changes — the service itself holds no data that could be corrupted by a bad deployment.
- **Implication**: Rollback is less critical for a stateless service than for stateful services. The primary risk is deploying a broken API that agents depend on, which can be mitigated by Kubernetes rollout undo.
- **Recommendation**: Document `kubectl rollout undo` and Helm rollback procedures for the deployment.
- **Evidence**: `Dockerfile` (deterministic build with pinned base image hash)

### ENG-Q4: API Test Coverage

- **Severity**: INFO
- **Finding**: `product_catalog_test.go` contains 4 unit tests: `TestGetProductExists`, `TestGetProductNotFound`, `TestListProducts`, and `TestSearchProducts`. Tests use a mock product catalog (4 products) and verify basic happy path and not-found scenarios. Tests cover all 3 RPCs.
- **Implication**: Core API contract is tested. No edge case testing (empty catalog, special characters), no error scenario testing (catalog load failures), no integration tests. Tests are not verified to run in CI.
- **Recommendation**: Expand test coverage with edge cases and error scenarios. Add tests to a CI pipeline.
- **Evidence**: `product_catalog_test.go` (4 tests: `TestGetProductExists`, `TestGetProductNotFound`, `TestListProducts`, `TestSearchProducts`)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The service exposes a well-defined gRPC interface via Protocol Buffers. `genproto/demo_grpc.pb.go` defines `ProductCatalogService` with three RPCs: `ListProducts`, `GetProduct`, and `SearchProducts`. gRPC with protobuf qualifies as a documented API interface. No direct database access, file-based exchange, or UI automation required.
- **Gap**: gRPC requires specific client libraries. No REST or HTTP/JSON alternative is provided.
- **Recommendation**: Consider adding a gRPC-Gateway or Envoy JSON transcoding proxy for agent frameworks that don't support native gRPC.
- **Evidence**: `genproto/demo_grpc.pb.go` (`ProductCatalogServiceServer` interface), `product_catalog.go` (implementation)

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: API defined via Protocol Buffers. Generated Go stubs in `genproto/`. Source `.proto` file not co-located — referenced at `../../protos/demo.proto` per `genproto.sh`.
- **Gap**: Canonical specification lives externally. No mechanism to verify generated stubs match source proto.
- **Recommendation**: Copy or symlink the `.proto` file into this repository. Add gRPC reflection for runtime schema discovery.
- **Evidence**: `genproto.sh` (`protodir=../../protos`), `genproto/demo_grpc.pb.go`, `genproto/demo.pb.go`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: gRPC status codes used: `codes.NotFound` for missing products, `codes.Unimplemented` for Watch. Limited to two error types. Catalog load failures return empty product lists silently.
- **Gap**: No rich error details. Silent failure on catalog load errors.
- **Recommendation**: Implement gRPC rich error model using `errdetails` package. Propagate catalog load errors as `codes.Internal`.
- **Evidence**: `product_catalog.go` (`status.Errorf(codes.NotFound, ...)`, `parseCatalog` returns empty on error)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No write operations. All three RPCs are read-only. Read operations are inherently idempotent.
- **Gap**: N/A for current scope.
- **Recommendation**: No action needed. Implement idempotency keys if write operations are added.
- **Evidence**: `product_catalog.go` (all RPCs are read-only)

#### API-Q5: Structured Response Format
- **Severity**: INFO
- **Finding**: Response format is Protocol Buffers binary over gRPC (HTTP/2). Strongly typed message structures: `ListProductsResponse`, `Product`, `SearchProductsResponse`, `Money`.
- **Gap**: Binary format is not human-readable but is type-safe and compact.
- **Recommendation**: Add gRPC reflection or JSON transcoding proxy for debugging.
- **Evidence**: `genproto/demo.pb.go` (message type definitions)

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
- **Finding**: No rate limit documentation or headers. No gRPC metadata indicating remaining request allowance or retry-after timing.
- **Gap**: Agents have no signal to self-throttle.
- **Recommendation**: Expose rate limit status via gRPC trailing metadata when rate limiting is implemented (STATE-Q5).
- **Evidence**: `server.go` (no rate limit metadata)

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: No machine identity authentication. `grpc.NewServer()` with no auth interceptors, no TLS, no mTLS. Outbound connections use `insecure.NewCredentials()`. Helm has `authorizationPolicies.create: false`. Any client reaching port 3550 can call all RPCs.
- **Gap**: No authentication mechanism. Cannot distinguish callers.
- **Recommendation**: Enable `authorizationPolicies.create: true` in Helm. Add gRPC server-side TLS and bearer token or mTLS authentication.
- **Evidence**: `server.go` (`grpc.NewServer()`, `insecure.NewCredentials()`), `product_catalog.go` (no auth checks), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No authorization model in application code. Helm AuthorizationPolicy template exists but `authorizationPolicies.create` is `false`.
- **Gap**: No scoped permissions enforced.
- **Recommendation**: Enable Istio AuthorizationPolicy. Add agent service accounts to allowed principals.
- **Evidence**: `product_catalog.go` (no permission checks), `helm-chart/values.yaml` (`authorizationPolicies.create: false`)

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No action-level authorization. Helm AuthorizationPolicy template (when enabled) is incomplete — missing `SearchProducts` path.
- **Gap**: Cannot restrict agents to specific methods.
- **Recommendation**: Update Helm AuthorizationPolicy to include all three RPC paths. Enable `authorizationPolicies.create: true`.
- **Evidence**: `product_catalog.go` (no permission checks), `helm-chart/templates/productcatalogservice.yaml` (missing SearchProducts)

#### AUTH-Q4: Identity Propagation and Delegation
- **Severity**: INFO
- **Finding**: No identity propagation. No JWT parsing, no OAuth2 on-behalf-of, no user context headers. No agent-as-self vs agent-on-behalf-of-user distinction. Archetype calibration: stateless-utility — downgraded to INFO.
- **Gap**: Cannot personalize responses per caller. Low impact for public catalog data.
- **Recommendation**: Implement identity propagation via gRPC metadata when user-specific filtering is needed.
- **Evidence**: `product_catalog.go` (context not inspected), `server.go` (no metadata interceptors)

#### AUTH-Q5: Credential Management
- **Severity**: RISK
- **Finding**: Mixed practices. Secret Manager used for AlloyDB password (good). `insecure.NewCredentials()` for outbound gRPC (bad). No TLS certificate management. No hardcoded credentials found.
- **Gap**: No TLS certificate management. Insecure outbound transport.
- **Recommendation**: Enable TLS on gRPC server. Replace `insecure.NewCredentials()` with TLS credentials.
- **Evidence**: `catalog_loader.go` (`getSecretPayload`), `server.go` (`insecure.NewCredentials()`)

#### AUTH-Q6: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured JSON logging via logrus (timestamp, severity, message) but no authenticated principal logged. No CloudTrail, no immutable log storage.
- **Gap**: Logs don't capture who made requests. No immutable log storage.
- **Recommendation**: After AUTH-Q1, add principal logging and configure immutable log storage.
- **Evidence**: `server.go` (logrus JSONFormatter — no principal field)

#### AUTH-Q7: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No identity suspension mechanism. No authentication exists to suspend.
- **Gap**: Cannot isolate a misbehaving agent without network-level blocking.
- **Recommendation**: When implementing AUTH-Q1, ensure per-agent identity revocation capability.
- **Evidence**: `server.go` (no auth model, no revocation)

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No compensation or rollback logic. All RPCs are read-only. Read operations are inherently safe.
- **Gap**: Not needed for current scope.
- **Recommendation**: No action for read-only scope. Implement if write operations are added.
- **Evidence**: `product_catalog.go` (all RPCs are read-only)

#### STATE-Q2: Queryable Current State
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `stateless-utility`, agent_scope: `read-only`.
- **Trigger**: Service has persistent state (stateful-crud, data-gateway, orchestrator)
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated

#### STATE-Q3: Concurrency Controls
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
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. gRPC server accepts unlimited concurrent connections on port 3550.
- **Gap**: No protection against runaway agent loops.
- **Recommendation**: Add gRPC rate limiting interceptor or deploy behind API Gateway with throttling.
- **Evidence**: `server.go` (`grpc.NewServer()` — no rate limiting)

#### STATE-Q6: Blast Radius and Transaction Limits ⚡
- **Severity**: INFO
- **Scope-Calibrated**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No transaction limits. No write operations exist, so no blast radius concern.
- **Gap**: N/A for current scope.
- **Recommendation**: Implement if write operations are added.
- **Evidence**: `product_catalog.go` (all RPCs read-only)

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
- **Finding**: No sandbox or staging environment. Single Dockerfile build target. No docker-compose. `products.json` serves all environments. For a stateless-utility serving static data, local testing is straightforward.
- **Gap**: No dedicated staging environment, but stateless nature makes local testing practical.
- **Recommendation**: Create docker-compose.yml for local testing. Deploy a separate staging instance.
- **Evidence**: `Dockerfile` (single target), `products.json` (single data file)

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Product catalog contains only public information: id, name, description, picture, price, categories. No PII, PHI, or credentials. Proto file includes `Data Classification: PUBLIC` comment. For a stateless-utility serving public reference data, formal field-level tags are low priority.
- **Gap**: No formal classification tags or policies.
- **Recommendation**: Formally classify as "Public/Non-Sensitive." Implement review process for new fields.
- **Evidence**: `products.json` (public fields only), `catalog_loader.go` (same fields from AlloyDB), `protos/demo.proto` (`Data Classification: PUBLIC`)

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: No residency configuration. AlloyDB region set via env vars. Product data is non-regulated. Read-only scope with public data — residency is informational only.
- **Gap**: No formal residency policy.
- **Recommendation**: Document data residency requirements alongside data classification.
- **Evidence**: `catalog_loader.go` (`PROJECT_ID`, `REGION` env vars), `products.json` (non-regulated data)

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
- **Finding**: No PII redaction or log scrubbing. Structured JSON logging configured but no filters. Product catalog data contains no PII. For a stateless-utility serving public data, absence of log scrubbing is low risk.
- **Gap**: No preventive PII redaction framework.
- **Recommendation**: Add logrus hook for PII pattern redaction as a preventive control.
- **Evidence**: `server.go` (logrus — no scrubbing), `products.json` (no PII)

#### DATA-Q7: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or profiling. `products.json` has 9 complete products with all fields populated. No monitoring for AlloyDB data quality.
- **Gap**: No quality monitoring as catalog grows.
- **Recommendation**: Implement data completeness checks for AlloyDB path.
- **Evidence**: `products.json` (9 complete products)

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Versioning and API Contracts
- **Severity**: INFO
- **Finding**: Schemas defined via protobuf. Generated code versioned in repo. Source `.proto` external (`../../protos/demo.proto`). Service registered as `hipstershop.ProductCatalogService` — no version prefix. No schema registry. No AlloyDB migration files. No breaking change detection in CI. For a stateless-utility with a small, stable API surface (3 read-only RPCs), the practical risk is lower.
- **Gap**: No API versioning strategy. Canonical schema not co-located.
- **Recommendation**: Adopt protobuf package versioning. Include `.proto` in this repo. Add `buf breaking` to CI.
- **Evidence**: `genproto/demo_grpc.pb.go` (`ServiceName: "hipstershop.ProductCatalogService"`), `genproto.sh`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are clear and human-readable: `id`, `name`, `description`, `picture`, `price_usd` (with `currency_code`, `units`, `nanos`), `categories`. No legacy abbreviations.
- **Gap**: None. Naming convention is excellent.
- **Recommendation**: Maintain this convention. Document `nanos` semantics.
- **Evidence**: `genproto/demo.pb.go` (Product fields), `products.json` (field names)

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No data catalog. No Glue, Collibra, Alation, or DataHub. No metadata files.
- **Gap**: Agent tool builders must examine source code to understand data semantics.
- **Recommendation**: Add data dictionary to README or SCHEMA.md.
- **Evidence**: `README.md` (no data dictionary)

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry tracing implemented but disabled by default. `ENABLE_TRACING=1` env var gates tracing, and Helm has `googleCloudOperations.tracing: false`. Structured JSON logging via logrus. No log-trace correlation.
- **Gap**: Tracing disabled in default deployment. Logs and traces not linked.
- **Recommendation**: Set `googleCloudOperations.tracing: true` in Helm. Add trace ID injection into log entries.
- **Evidence**: `server.go` (`ENABLE_TRACING`, `initTracing()`, logrus), `helm-chart/values.yaml` (`tracing: false`)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. No CloudWatch alarms, no Prometheus rules, no incident management integration.
- **Gap**: API degradation will not trigger alerts.
- **Recommendation**: Configure alerting on gRPC error rates and P95 latency.
- **Evidence**: No alerting files found. `server.go` (no alerting)

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. No custom metrics for catalog queries, search effectiveness, or product views.
- **Gap**: No signal for agent interaction quality.
- **Recommendation**: Add metrics for search-hit-rate, products-viewed, empty-result-rate.
- **Evidence**: `server.go` (no custom metrics), `product_catalog.go` (no instrumentation)

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Helm chart defines Deployment, Service, NetworkPolicy, Istio Sidecar, and AuthorizationPolicy. AuthorizationPolicies disabled (`authorizationPolicies.create: false`). No drift detection. Helm chart not co-located with service source.
- **Gap**: Security surface ungoverned. No drift detection.
- **Recommendation**: Enable `authorizationPolicies.create: true`. Add drift detection.
- **Evidence**: `helm-chart/templates/productcatalogservice.yaml`, `helm-chart/values.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: No CI/CD in service directory. Parent repo has `cloudbuild.yaml` but no protobuf breaking change detection. No contract testing.
- **Gap**: No automated contract testing to protect agents from breaking changes.
- **Recommendation**: Add `buf breaking` to CI. Add contract tests for gRPC service behavior.
- **Evidence**: No CI/CD in service directory. `cloudbuild.yaml` (parent repo)

#### ENG-Q3: Rollback Capability
- **Severity**: INFO
- **Finding**: No rollback configuration. No blue/green, no feature flags. Dockerfile uses pinned base image hash. For a stateless-utility with no persistent state, rollback risk is limited to API contract changes.
- **Gap**: No defined rollback procedure, but stateless nature limits impact.
- **Recommendation**: Document `kubectl rollout undo` and Helm rollback procedures.
- **Evidence**: `Dockerfile` (deterministic build with pinned base image)

#### ENG-Q4: API Test Coverage
- **Severity**: INFO
- **Finding**: 4 unit tests in `product_catalog_test.go`: TestGetProductExists, TestGetProductNotFound, TestListProducts, TestSearchProducts. Cover all 3 RPCs with happy path and not-found scenarios.
- **Gap**: No edge cases, no error scenarios, no integration tests, no CI execution.
- **Recommendation**: Add edge case and error scenario tests. Add to CI pipeline.
- **Evidence**: `product_catalog_test.go` (4 tests)

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
| `helm-chart/templates/productcatalogservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q3, ENG-Q1 |
| `helm-chart/values.yaml` | AUTH-Q1, AUTH-Q2, OBS-Q1, ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `server.go` | API-Q1, API-Q8, AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q5, DATA-Q6, OBS-Q1, OBS-Q2, OBS-Q3 |
| `product_catalog.go` | API-Q1, API-Q3, API-Q4, AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, STATE-Q1, STATE-Q5, STATE-Q6, HITL-Q3, DATA-Q1 |
| `catalog_loader.go` | AUTH-Q5, DATA-Q1, DATA-Q2 |
| `product_catalog_test.go` | ENG-Q4 |
| `genproto/demo_grpc.pb.go` | API-Q1, API-Q2, API-Q4, AUTH-Q3, DISC-Q1 |
| `genproto/demo.pb.go` | API-Q2, API-Q5, DISC-Q2 |
| `genproto.sh` | API-Q2, DISC-Q1 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | DATA-Q1, DISC-Q1 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | HITL-Q3, ENG-Q3 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | OBS-Q1, OBS-Q2 |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `products.json` | DATA-Q1, DATA-Q2, DATA-Q6, DATA-Q7, DISC-Q2, HITL-Q3 |

### Documentation
| File | Questions Referenced |
|------|---------------------|
| `README.md` | DISC-Q3 |
