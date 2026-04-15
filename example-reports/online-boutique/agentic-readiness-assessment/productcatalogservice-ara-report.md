# Agentic Readiness Assessment Report

**Target**: productcatalogservice (./services/microservices-demo/src/productcatalogservice)
**Date**: 2026-04-15
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: application
**Agent Scope**: read-only
**Priority**: P0
**Tags**: go, grpc, catalog
**Context**: Go gRPC service serving product catalog from a JSON file.

---

## Readiness Profile: Remediation Required

**BLOCKERs**: 2 | **RISKs**: 30 | **INFOs**: 17

Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days.

---

## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | 2 |
| RISK | 30 |
| INFO | 17 |
| N/A | 0 |
| **Total** | **49** |

**Questions Evaluated**: 49
**Questions N/A (repo_type: application)**: 0

---

## BLOCKERs — Must Resolve Before Agent Deployment

### AUTH-Q1: Machine Identity Authentication

- **Severity**: BLOCKER
- **Finding**: The gRPC server is initialized with `grpc.NewServer()` with only an OpenTelemetry stats handler — no authentication interceptors, no TLS, no token validation. The client connection to the OTel collector uses `insecure.NewCredentials()`. The Kubernetes ServiceAccount `productcatalogservice` is defined but has no IAM annotations or Workload Identity bindings. Any caller with network access to port 3550 can invoke all RPCs without authentication.
- **Gap**: No authentication mechanism exists. The service cannot identify which agent or caller made a request. There is no machine identity, no API key validation, no OAuth2 client credentials flow, no mTLS, and no principal attribution in logs.
- **Remediation**:
  - **Immediate**: Add a gRPC unary interceptor that validates an authentication token (JWT or API key) on every incoming request. Use GKE Workload Identity to bind the Kubernetes ServiceAccount to a Google Cloud IAM service account for downstream calls.
  - **Target State**: Every gRPC call is authenticated with a principal identity that is logged in structured log entries. Agent identities are distinguishable from human and other service identities.
  - **Estimated Effort**: Medium (2–4 weeks)
  - **Dependencies**: ENG-Q6 (network policies must be enforced alongside auth to provide defense in depth)
- **Evidence**: `server.go` (line: `srv = grpc.NewServer(grpc.StatsHandler(otelgrpc.NewServerHandler()))`), `server.go` (`insecure.NewCredentials()`), `kubernetes-manifests/productcatalogservice.yaml` (ServiceAccount with no IAM annotations)

### ENG-Q6: Cross-Origin and Network Policies

- **Severity**: BLOCKER
- **Finding**: The Kubernetes Service is ClusterIP (internal only), which limits exposure. Network policies exist in `kustomize/components/network-policies/network-policy-productcatalogservice.yaml` — they restrict ingress to only `frontend`, `checkoutservice`, and `recommendationservice` pods on port 3550, with a default deny-all policy. However, these network policies are **optional** — they are only applied when using the `network-policies` Skaffold profile (`skaffold run -p network-policies`). They are not part of the default deployment. Additionally, the gRPC server uses insecure credentials (no TLS) and Istio service mesh configuration exists only for the frontend service, not for productcatalogservice.
- **Gap**: Network policies are not enforced by default. The default `skaffold run` or `kubectl apply -k kubernetes-manifests/` deploys without any network segmentation. The gRPC server transmits data in plaintext (no mTLS, no TLS). The network security configuration is discoverable in the repo but not active unless explicitly opted in.
- **Remediation**:
  - **Immediate**: Make network policies part of the default deployment by moving them from the optional Skaffold profile into the base Kustomize manifests. Enable Istio sidecar injection for the productcatalogservice namespace to get automatic mTLS between services.
  - **Target State**: Network policies are always active (deny-all default with explicit allow rules). All inter-service communication uses mTLS via Istio or equivalent. The security posture is the default, not an opt-in profile.
  - **Estimated Effort**: Low (1–2 weeks)
  - **Dependencies**: AUTH-Q1 (authentication at the application layer provides defense in depth alongside network policies)
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml` (ClusterIP Service), `kustomize/components/network-policies/network-policy-productcatalogservice.yaml` (ingress restricted to frontend/checkoutservice/recommendationservice), `kustomize/components/network-policies/network-policy-deny-all.yaml` (deny-all baseline), `skaffold.yaml` (network-policies as optional profile), `server.go` (`insecure.NewCredentials()`), `istio-manifests/` (frontend only)

---

## RISKs — Proceed with Compensating Controls

### API-Q2: Machine-Readable API Specification

- **Severity**: RISK
- **Finding**: The protobuf definition `protos/demo.proto` serves as the machine-readable interface specification. It defines 3 RPCs (ListProducts, GetProduct, SearchProducts) with typed request/response messages. Generated Go code exists in `genproto/demo.pb.go` and `genproto/demo_grpc.pb.go`. The proto file is the source of truth for the API contract.
- **Gap**: The proto file is manually maintained alongside the generated code. There is no schema registry, no validation that the proto and generated code are in sync, and no versioning of the proto definition. gRPC server reflection is not enabled, which would allow runtime introspection.
- **Compensating Controls**:
  - Use `buf` or `prototool` to lint and validate proto files in CI
  - Enable gRPC server reflection for runtime introspection by agents
- **Remediation Timeline**: 30 days
- **Recommendation**: Add proto validation to the CI pipeline using `buf lint` and `buf breaking` to detect breaking changes. Enable gRPC server reflection in `server.go`.
- **Evidence**: `protos/demo.proto`, `genproto/demo.pb.go`, `genproto/demo_grpc.pb.go`, `genproto.sh`

### API-Q3: Structured Error Responses

- **Severity**: RISK
- **Finding**: The service uses gRPC status codes: `codes.NotFound` for missing products (in `GetProduct`) and `codes.Unimplemented` for unsupported methods (in `Watch`). Error messages include context (e.g., "no product with ID %s"). The gRPC status framework provides code + message but no additional structured error details.
- **Gap**: No custom error details, no retryable boolean, no error category classification. Agents cannot distinguish retriable errors from terminal errors without interpreting gRPC status codes directly. The error handling is minimal — only `NotFound` and `Unimplemented` are explicitly handled; other errors (catalog load failures) return empty product lists silently rather than propagating errors.
- **Compensating Controls**:
  - Map gRPC status codes to retry decisions at the agent tool layer (e.g., UNAVAILABLE → retry, NOT_FOUND → terminal)
  - Add gRPC error details using `google.rpc.Status` with rich error model
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Use gRPC rich error model (`errdetails` package) to attach structured error information including error type, retryability, and debug info. Propagate catalog loading failures as gRPC errors instead of returning empty results.
- **Evidence**: `product_catalog.go` (`status.Errorf(codes.NotFound, ...)`, `status.Errorf(codes.Unimplemented, ...)`), `product_catalog.go` (`parseCatalog` returns empty slice on error)

### API-Q5: API Versioning and Deprecation

- **Severity**: RISK
- **Finding**: The gRPC package is `hipstershop` with no version suffix. No API versioning is implemented — no `/v1/` path prefix, no version fields in the proto package name, and no deprecation policy. Protobuf field numbers provide backward-compatible wire encoding, but there is no semantic versioning of the API surface.
- **Gap**: No versioning strategy. No deprecation policy. No changelog tracking API changes. Breaking changes to the proto definition would silently break all consumers.
- **Compensating Controls**:
  - Use `buf breaking` in CI to prevent breaking proto changes
  - Pin agent tool definitions to specific proto file hashes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Adopt proto package versioning (e.g., `hipstershop.v1`). Add `buf breaking` to the CI pipeline to detect and block breaking changes. Maintain a CHANGELOG for the API surface.
- **Evidence**: `protos/demo.proto` (`package hipstershop;` — no version suffix), no CHANGELOG file found

### API-Q7: Asynchronous Operation Support

- **Severity**: RISK
- **Finding**: All 3 RPCs (ListProducts, GetProduct, SearchProducts) are synchronous unary calls. No streaming RPCs, no async job patterns, no polling endpoints, no webhook callbacks. The `EXTRA_LATENCY` environment variable can inject artificial delay but there are no async patterns for long-running operations.
- **Gap**: No asynchronous operation support. For a read-only catalog service, synchronous responses are acceptable if latency is low (sub-second for JSON file reads). However, the AlloyDB data path introduces network latency with no timeout or async fallback.
- **Compensating Controls**:
  - Set agent-side timeouts on gRPC calls (e.g., 5-second deadline)
  - Implement client-side caching for catalog data
- **Remediation Timeline**: 60–90 days (if needed)
- **Recommendation**: Add gRPC deadlines on the server side. For the AlloyDB path, consider implementing a cache-aside pattern with periodic refresh to ensure consistent low-latency responses.
- **Evidence**: `product_catalog.go` (all RPCs are synchronous unary), `server.go` (`EXTRA_LATENCY` env var)

### AUTH-Q2: Scoped Permissions (Least Privilege)

- **Severity**: RISK
- **Finding**: No permission model exists within the application. The Kubernetes ServiceAccount `productcatalogservice` is defined but has no associated Role, RoleBinding, or IAM policy bindings. The Terraform provisions a GKE Autopilot cluster but defines no workload-specific IAM roles. All RPCs are accessible to any authenticated caller (once AUTH-Q1 is resolved).
- **Gap**: No scoped permissions. Once a caller can reach the service, they can invoke all 3 RPCs. There is no mechanism to grant read-only access to specific endpoints or restrict access per resource type.
- **Compensating Controls**:
  - Implement gRPC interceptor-based authorization that checks caller identity against an allow list per RPC method
  - Use Istio AuthorizationPolicy to restrict which services can call specific RPCs
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Define Istio AuthorizationPolicy rules that restrict which source workloads can invoke each RPC. Bind the Kubernetes ServiceAccount to a GCP IAM service account with minimal permissions using Workload Identity.
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml` (ServiceAccount with no bindings), `terraform/main.tf` (no IAM roles for workloads)

### AUTH-Q3: Action-Level Authorization

- **Severity**: RISK
- **Finding**: No authorization checks exist in the service code. All 3 RPCs are open to any caller. There are no middleware checks, no RBAC definitions, no ABAC policies, and no permission matrices.
- **Gap**: No action-level authorization. An agent identity cannot be restricted to only `GetProduct` while being denied `ListProducts` or `SearchProducts` at the application level.
- **Compensating Controls**:
  - Use Istio AuthorizationPolicy with method-level rules (e.g., allow agent X to call `GetProduct` but not `ListProducts`)
  - Implement a gRPC authorization interceptor with a configurable policy
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a gRPC unary interceptor that performs method-level authorization based on the caller's identity and a configurable permission policy.
- **Evidence**: `product_catalog.go` (no authorization checks in ListProducts, GetProduct, SearchProducts)

### AUTH-Q4: Identity Propagation

- **Severity**: RISK
- **Finding**: No token parsing, JWT validation, or user context extraction exists. The gRPC methods do not read any identity from the incoming `context.Context`. The service does not propagate caller identity to downstream calls (AlloyDB, OTel collector).
- **Gap**: No identity propagation. An agent acting on behalf of a specific user cannot pass that user's context through the service. All requests are anonymous.
- **Compensating Controls**:
  - Pass user context via gRPC metadata headers (e.g., `x-user-id`) validated at the gateway layer
  - Use Istio to inject authenticated identity into request headers
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Extract caller identity from gRPC metadata or JWT claims in an interceptor and include it in structured log entries for audit purposes.
- **Evidence**: `product_catalog.go` (context parameter unused for identity), `server.go` (no identity extraction)

### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User

- **Severity**: RISK
- **Finding**: No distinction between caller types exists. The service has no concept of identity at all (see AUTH-Q1), so there is no way to differentiate between an agent acting under its own identity and an agent acting on behalf of a user.
- **Gap**: No agent mode differentiation. No separate auth flows, no distinct audit log fields, no separate IAM roles for the two modes.
- **Compensating Controls**:
  - Define separate API keys or service accounts for agent-as-self vs agent-on-behalf-of-user patterns
  - Use different gRPC metadata headers for the two modes
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1 resolution)
- **Recommendation**: After implementing authentication (AUTH-Q1), define two distinct caller identity patterns: (1) agent service account for autonomous operations, (2) user-delegated token for on-behalf-of operations. Log the mode in audit entries.
- **Evidence**: `product_catalog.go`, `server.go` (no identity handling)

### AUTH-Q6: Credential Management

- **Severity**: RISK
- **Finding**: The AlloyDB code path uses Google Cloud Secret Manager to retrieve the database password (`getSecretPayload` function in `catalog_loader.go`), which is proper secrets management. No hardcoded credentials were found in source code. However, AlloyDB connection parameters (cluster name, instance name, project ID, region) are passed via environment variables which are visible in the pod spec. The local file path has no credentials.
- **Gap**: While Secret Manager is used for the database password, there is no credential rotation mechanism visible. Environment variables for AlloyDB configuration (non-secret but sensitive) are set at the pod level. No `.env` files are committed to git (positive).
- **Compensating Controls**:
  - Configure Secret Manager automatic rotation for the AlloyDB password
  - Use Kubernetes Secrets (encrypted at rest in GKE) for sensitive environment variables
- **Remediation Timeline**: 30 days
- **Recommendation**: Enable automatic secret rotation in Secret Manager. Ensure the service handles rotated credentials gracefully (e.g., connection pool refresh). Move sensitive environment variables to Kubernetes Secrets backed by Secret Manager.
- **Evidence**: `catalog_loader.go` (`getSecretPayload` function using `secretmanager.NewClient`), `kubernetes-manifests/productcatalogservice.yaml` (env vars for PORT, DISABLE_PROFILER)

### AUTH-Q7: Immutable Audit Logging ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The service uses logrus with JSON formatting (`JSONFormatter`) outputting structured logs with timestamp, severity, and message fields. However, no audit-specific logging exists — the service does not log the authenticated principal for any request. No CloudTrail configuration, no immutable log storage, and no tamper-evident logging are configured in the Terraform or Kubernetes manifests.
- **Gap**: No audit logging of caller identity per request. No immutable log storage. Structured logging exists but does not capture who made each call or what they accessed. The Terraform enables Cloud Trace and Cloud Profiler APIs but not Cloud Audit Logs or Cloud Logging with immutability.
- **Compensating Controls**:
  - Enable GKE audit logging at the cluster level (Terraform)
  - Configure Cloud Logging with log buckets that have retention locks
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a gRPC logging interceptor that records caller identity, method, timestamp, and request metadata for every RPC call. Configure log export to an immutable storage destination (Cloud Storage with bucket lock or BigQuery).
- **Evidence**: `server.go` (logrus JSONFormatter), `terraform/main.tf` (no audit logging configuration), `kubernetes-manifests/productcatalogservice.yaml` (no audit annotations)

### AUTH-Q8: Agent Identity Suspension

- **Severity**: RISK
- **Finding**: No agent identity management exists since there is no authentication mechanism (AUTH-Q1). There is no mechanism to suspend, revoke, or disable individual caller access. The only way to block a caller is to modify network policies or shut down the service entirely.
- **Gap**: No individual identity suspension. Cannot isolate a misbehaving agent without affecting all consumers.
- **Compensating Controls**:
  - Use Istio AuthorizationPolicy to block specific source workloads dynamically
  - Implement API key revocation once AUTH-Q1 is resolved
- **Remediation Timeline**: 60–90 days (depends on AUTH-Q1)
- **Recommendation**: After implementing authentication, add an API key or token revocation mechanism that can disable individual agent identities within minutes. Integrate with an alerting system to trigger automatic suspension on anomaly detection.
- **Evidence**: `server.go` (no auth interceptor, no identity management)

### STATE-Q1: Compensation and Rollback ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: The productcatalogservice is a read-only catalog service with no write operations. The 3 RPCs (ListProducts, GetProduct, SearchProducts) only read data. There are no multi-step write workflows, no saga patterns, no compensation logic, and no undo endpoints — because there are no write operations to compensate for.
- **Gap**: No compensation or rollback mechanisms exist. While this is expected for a read-only service, the absence means the service cannot support write-enabled agent scenarios without significant architecture changes.
- **Compensating Controls**:
  - Maintain read-only agent scope for this service (no write operations needed)
  - If write operations are added in the future, implement saga pattern with explicit compensation endpoints
- **Remediation Timeline**: Not immediately required for read-only agent scope
- **Recommendation**: Document the read-only nature of this service in the agent tool definition. If catalog management write operations are needed in the future, design them with idempotency and compensation from the start.
- **Evidence**: `product_catalog.go` (only read RPCs: ListProducts, GetProduct, SearchProducts)

### STATE-Q4: Circuit Breakers and Resilience

- **Severity**: RISK
- **Finding**: No circuit breakers, retry logic, or explicit timeout configurations exist for external dependency calls. The AlloyDB connection has no retry logic — if AlloyDB is unavailable, catalog loading fails immediately. The gRPC connection to the OTel collector has a 3-second context timeout but no retry or circuit breaker. The profiler initialization has a retry loop (3 attempts with exponential backoff) but this is not for data path calls.
- **Gap**: No resilience patterns for the data path. A transient AlloyDB failure causes the catalog to fail to load, and the service returns empty product lists to callers with no error signal (see API-Q3).
- **Compensating Controls**:
  - Implement a cache of the last successfully loaded catalog to serve stale data during AlloyDB outages
  - Configure Istio retry and circuit breaker policies for upstream connections
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add a retry mechanism with exponential backoff for AlloyDB connections. Implement a local cache that serves the last known good catalog when the data source is unavailable. Add circuit breaker logic to prevent cascading failures.
- **Evidence**: `catalog_loader.go` (no retry on AlloyDB failure), `server.go` (`mustConnGRPC` with 3s timeout, no retry), `server.go` (profiler retry is non-data-path)

### STATE-Q5: Rate Limiting and Throttling

- **Severity**: RISK
- **Finding**: No rate limiting at any layer. No API Gateway in front of the gRPC service. No gRPC interceptors for throttling. No application-level rate limiting middleware. The Kubernetes manifest defines CPU/memory resource limits (200m CPU, 128Mi memory) which provide natural resource bounding but not explicit request-level rate limiting.
- **Gap**: No protection against runaway agent loops. An agent calling ListProducts in a tight loop could exhaust the service's CPU allocation and degrade service for all consumers.
- **Compensating Controls**:
  - Deploy an API Gateway or gRPC proxy (e.g., Envoy) with rate limiting
  - Configure Istio rate limiting using `EnvoyFilter`
- **Remediation Timeline**: 30 days
- **Recommendation**: Add a gRPC interceptor for rate limiting per caller identity, or configure Istio/Envoy rate limiting at the mesh level. Set limits appropriate for catalog read patterns (e.g., 100 requests/minute per agent identity).
- **Evidence**: `server.go` (no rate limiting), `kubernetes-manifests/productcatalogservice.yaml` (resource limits only)

### STATE-Q6: Blast Radius and Transaction Limits

- **Severity**: RISK
- **Finding**: No configurable transaction limits or blast radius controls. As a read-only service, the blast radius is limited to resource exhaustion (CPU, memory) rather than data corruption. No agent-specific limits, no maximum records per query, no per-agent quotas.
- **Gap**: No agent-specific limits on request volume or data retrieval. ListProducts returns all 9 products without pagination, and SearchProducts returns all matching products. While the dataset is small, there are no controls if the catalog grows significantly or if AlloyDB contains a larger dataset.
- **Compensating Controls**:
  - Implement pagination on ListProducts and SearchProducts to bound result set size
  - Set per-agent rate limits at the gateway layer
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination support to ListProducts and SearchProducts RPCs. Define maximum result set sizes. Consider per-agent quotas if multiple agents will consume this service.
- **Evidence**: `product_catalog.go` (ListProducts returns all products, SearchProducts returns all matches), `products.json` (9 products currently)

### STATE-Q7: Infrastructure Capacity for Agent Traffic

- **Severity**: RISK
- **Finding**: No load testing results found. No auto-scaling policies configured. The Kubernetes Deployment does not specify a replica count (defaults to 1) and no Horizontal Pod Autoscaler (HPA) is defined. Resource requests are modest (100m CPU, 64Mi memory) with limits at 200m CPU and 128Mi memory. The GKE Autopilot cluster handles node-level scaling but pod-level autoscaling is not configured.
- **Gap**: Single replica with no HPA means a single pod failure causes full outage. No load testing validates the service can handle agent traffic patterns. Resource limits are conservative and may be insufficient for concurrent agent requests.
- **Compensating Controls**:
  - Deploy with multiple replicas (minimum 2 for availability)
  - Configure HPA based on CPU utilization
- **Remediation Timeline**: 30 days
- **Recommendation**: Define a minimum of 2 replicas and configure HPA with CPU/memory targets. Run load tests simulating agent traffic patterns (concurrent reads, burst patterns). Increase resource limits if needed.
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml` (no replica count, no HPA, resource limits: 200m CPU/128Mi memory)

### HITL-Q3: Sandbox/Staging Environment

- **Severity**: RISK
- **Finding**: The CI/CD pipeline (`ci-pr.yaml`) deploys to PR-specific namespaces in a staging GKE cluster (`prs-gke-cluster`), providing an isolated staging-like environment for each pull request. Skaffold supports local development with `skaffold dev`. However, there is no dedicated persistent staging environment with production-equivalent data, no seed data scripts, and no synthetic data generators.
- **Gap**: PR-specific ephemeral environments exist but are not persistent staging environments. No production-equivalent data shape for agent testing. An agent cannot be tested against realistic catalog data in a dedicated staging environment.
- **Compensating Controls**:
  - Use the PR-based deployment mechanism to create a persistent staging namespace
  - Copy production `products.json` to staging environments
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Create a persistent staging environment with production-equivalent data (either the full `products.json` or AlloyDB with representative data). Document the staging environment for agent integration testing.
- **Evidence**: `.github/workflows/ci-pr.yaml` (PR-specific namespace deployment), `skaffold.yaml` (local development support)

### DATA-Q2: Data Residency and Sovereignty ⚡

- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements are documented. The GKE cluster region defaults to `us-central1` (configurable via Terraform variable). The AlloyDB instance region is configured via environment variable. Product catalog data (product names, descriptions, prices, categories) is not typically subject to data residency or sovereignty requirements — it is public product information.
- **Gap**: No data residency controls or documentation. If the catalog were to contain region-specific pricing or localized content, there would be no controls preventing cross-region data transmission to an LLM provider.
- **Compensating Controls**:
  - Document that product catalog data is non-sensitive public information not subject to residency requirements
  - If residency requirements emerge, configure the LLM endpoint in the same region as the data source
- **Remediation Timeline**: Not immediately required for non-sensitive catalog data
- **Recommendation**: Document the data residency posture for the product catalog. If AlloyDB data includes customer-specific or region-specific information in the future, implement data residency controls before agent integration.
- **Evidence**: `terraform/variables.tf` (region default: us-central1), `catalog_loader.go` (REGION env var for AlloyDB), `products.json` (public product data)

### DATA-Q3: Selective Query Support

- **Severity**: RISK
- **Finding**: `GetProduct` supports single-item lookup by ID (selective). `SearchProducts` supports text search on name and description fields. However, `ListProducts` returns ALL products with no pagination, no filtering, no sorting, and no result size limits. `SearchProducts` also returns all matching products with no pagination.
- **Gap**: No pagination on ListProducts or SearchProducts. No filter parameters beyond the search query. No sorting options. No cursor-based pagination. For the current 9-product catalog this is manageable, but the AlloyDB path could serve a much larger dataset.
- **Compensating Controls**:
  - Use `GetProduct` for specific lookups (bounded result)
  - Implement client-side pagination for ListProducts results
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add pagination parameters (limit, offset or cursor) to `ListProducts` and `SearchProducts` RPCs in the proto definition. Add filter and sort capabilities.
- **Evidence**: `product_catalog.go` (ListProducts returns all products, SearchProducts returns all matches), `protos/demo.proto` (no pagination fields in request messages)

### DATA-Q4: System of Record Designations

- **Severity**: RISK
- **Finding**: No system-of-record documentation exists. The product catalog data can be loaded from two sources: a local JSON file (`products.json`) or AlloyDB. There is no documentation specifying which is authoritative. The loading logic in `loadCatalog` prioritizes AlloyDB if `ALLOYDB_CLUSTER_NAME` is set, otherwise falls back to the local file.
- **Gap**: No golden record designation. No conflict resolution between the JSON file and AlloyDB. If both contain different data, there is no documented policy for which takes precedence beyond the runtime logic.
- **Compensating Controls**:
  - Document AlloyDB as the system of record when configured; otherwise products.json is authoritative
  - Remove the dual-source ambiguity by choosing a single source of truth
- **Remediation Timeline**: 30 days
- **Recommendation**: Designate either AlloyDB or the JSON file as the authoritative source of product data and document it. If AlloyDB is the target state, remove the JSON fallback in production deployments.
- **Evidence**: `catalog_loader.go` (`loadCatalog` checks `ALLOYDB_CLUSTER_NAME` env var to choose source), `products.json` (local data)

### DATA-Q5: Reliable Timestamps

- **Severity**: RISK
- **Finding**: No timestamps on product records. The `Product` message in `demo.proto` contains: id, name, description, picture, price_usd, and categories — no `created_at`, `updated_at`, or `event_time` fields. The JSON file has no temporal metadata. There is no way for an agent to determine when a product was added, last modified, or when price changed.
- **Gap**: No temporal data on any product record. Agents performing time-sensitive reasoning (e.g., "which products were updated this week?") cannot operate.
- **Compensating Controls**:
  - Use the file modification timestamp of `products.json` as a proxy for "last catalog update"
  - If AlloyDB is used, add timestamp columns to the product table
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `created_at` and `updated_at` fields to the `Product` protobuf message and database schema. Store timestamps in UTC with RFC3339 format.
- **Evidence**: `protos/demo.proto` (Product message has no timestamp fields), `products.json` (no timestamps), `catalog_loader.go` (AlloyDB query selects no timestamp columns)

### DATA-Q6: Data Freshness Signaling

- **Severity**: RISK
- **Finding**: No data freshness indicators are returned in gRPC responses. No cache headers, no `last_refreshed` field, no `data_age` metadata. The catalog reload mechanism (SIGUSR1/SIGUSR2 signals) controls when the catalog is refreshed but provides no signal to consumers about data freshness. The `parseCatalog` function reloads on every request when `reloadCatalog` is true, but consumers have no way to know whether they are receiving freshly loaded or cached data.
- **Gap**: No freshness signaling. An agent cannot determine if the product data is current, stale, or from a cached load. The dual source (JSON/AlloyDB) adds ambiguity about data age.
- **Compensating Controls**:
  - Add a `last_loaded_at` timestamp to the ListProductsResponse as gRPC trailing metadata
  - Include data source information (JSON file vs AlloyDB) in response metadata
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add gRPC response metadata indicating data source, last load time, and catalog version. Consider adding an `If-None-Match`/ETag equivalent for catalog caching.
- **Evidence**: `product_catalog.go` (`parseCatalog` reloads when `reloadCatalog` is true), `server.go` (SIGUSR1/SIGUSR2 signal handling)

### DISC-Q1: Schema Documentation and Versioning

- **Severity**: RISK
- **Finding**: The protobuf definition (`protos/demo.proto`) serves as schema documentation. Protobuf field numbers provide wire-level backward compatibility. The generated Go code in `genproto/` is checked into the repository. The `genproto.sh` script documents how to regenerate from the proto definition.
- **Gap**: No semantic versioning of the schema. No schema registry. No schema evolution tracking (no changelog for proto changes). The proto file serves the entire microservices-demo application, not just productcatalogservice — changes to any service's proto definitions are in the same file.
- **Compensating Controls**:
  - Use `buf` schema registry to version and track proto changes
  - Add `buf breaking` to CI to prevent unintentional breaking changes
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Split the monolithic `demo.proto` into per-service proto files. Adopt `buf` for schema management, linting, and breaking change detection. Version proto packages (e.g., `hipstershop.productcatalog.v1`).
- **Evidence**: `protos/demo.proto` (monolithic proto for all services), `genproto.sh` (code generation script), `genproto/demo.pb.go`

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface

- **Severity**: RISK
- **Finding**: Infrastructure is partially defined as code: (1) Terraform provisions the GKE Autopilot cluster (`terraform/main.tf`), (2) Kubernetes manifests define the Deployment, Service, and ServiceAccount (`kubernetes-manifests/productcatalogservice.yaml`), (3) Network policies are defined in Kustomize components. A Terraform validation CI workflow exists (`terraform-validate-ci.yaml`) that runs `terraform init` and `terraform validate` on PR. However: no drift detection is configured, no Terraform plan review in PR comments, and Kubernetes manifest changes are not subject to policy validation.
- **Gap**: (1) IaC definition: partially present ✓. (2) Change review: Terraform validation exists but no plan output review; Kubernetes manifest changes have no automated policy validation. (3) Drift detection: not configured.
- **Compensating Controls**:
  - Add Terraform plan output to PR comments for review
  - Implement OPA/Gatekeeper policies for Kubernetes manifest validation
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `terraform plan` output to PRs. Implement drift detection (e.g., `driftctl` or Cloud Asset Inventory). Add OPA/Gatekeeper policy checks for Kubernetes manifests in CI.
- **Evidence**: `terraform/main.tf` (GKE cluster), `kubernetes-manifests/productcatalogservice.yaml` (k8s resources), `.github/workflows/terraform-validate-ci.yaml` (terraform init + validate only)

### ENG-Q2: CI/CD with API Contract Testing

- **Severity**: RISK
- **Finding**: CI pipeline exists (`ci-pr.yaml`, `ci-main.yaml`) with Go unit tests for productcatalogservice (`go test`). Unit tests validate basic API behavior: GetProduct (found/not found), ListProducts (count), SearchProducts (query matching). However, no API contract testing (Pact, proto schema validation), no breaking change detection for the proto definition, and no consumer-driven contract tests.
- **Gap**: No proto breaking change detection in CI. No consumer-driven contract tests. Unit tests validate implementation behavior but not the API contract stability that agents depend on.
- **Compensating Controls**:
  - Add `buf breaking` check in CI to detect proto contract changes
  - Add integration tests that validate against the proto definition
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add `buf breaking --against .git#branch=main` to the CI pipeline. Implement integration tests that validate gRPC responses against the proto schema.
- **Evidence**: `.github/workflows/ci-pr.yaml` (Go unit tests), `product_catalog_test.go` (4 test cases), `.github/workflows/ci-main.yaml` (Go unit tests)

### ENG-Q3: Rollback Capability

- **Severity**: RISK
- **Finding**: Deployment uses Skaffold with Kustomize and `kubectl apply`. Cloud Build supports deployment via Skaffold. The CI pipeline deploys to PR-specific namespaces. However, no blue/green or canary deployment is configured. No automated rollback triggers. No feature flags. Skaffold does not configure rollback behavior. The Kubernetes Deployment has no rollback strategy defined beyond the default `kubectl rollout undo`.
- **Gap**: No automated rollback capability. A broken deployment requires manual intervention (`kubectl rollout undo`). No canary deployment to catch issues before full rollout. No deployment health checks that trigger automatic rollback.
- **Compensating Controls**:
  - Use `kubectl rollout undo` for manual rollback
  - Pin Skaffold image tags to known-good versions
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Configure Kubernetes Deployment with `maxUnavailable: 0` for zero-downtime deploys. Implement canary deployment using Istio traffic splitting. Add automated rollback triggers based on health check failures.
- **Evidence**: `skaffold.yaml` (kubectl deploy, no rollback config), `cloudbuild.yaml` (skaffold run, no rollback), `kubernetes-manifests/productcatalogservice.yaml` (no deployment strategy specified)

### ENG-Q4: API Test Coverage

- **Severity**: RISK
- **Finding**: Unit tests exist in `product_catalog_test.go` covering 4 scenarios: GetProduct (product exists), GetProduct (product not found), ListProducts (returns correct count), SearchProducts (query matching). Tests use mock data (4 products) and validate against the in-memory catalog. Tests run in CI (`ci-pr.yaml`, `ci-main.yaml`).
- **Gap**: No edge case testing (empty search query, special characters, very long queries). No error response format testing. No load testing. No integration tests against AlloyDB. No tests for catalog reload behavior (SIGUSR1/SIGUSR2). Tests cover happy path and one error case only.
- **Compensating Controls**:
  - The existing 4 test cases provide baseline confidence for core read operations
  - Add integration tests incrementally
- **Remediation Timeline**: 30–60 days
- **Recommendation**: Add test cases for: empty catalog handling, concurrent requests during catalog reload, AlloyDB connection failure handling, malformed product IDs, empty search queries. Add benchmarks to measure latency under load.
- **Evidence**: `product_catalog_test.go` (4 test functions), `.github/workflows/ci-pr.yaml` (`go test` step)

### ENG-Q5: Encryption at Rest for Agent-Accessible Data

- **Severity**: RISK
- **Finding**: The product catalog JSON file is embedded in the container image via `COPY products.json .` in the Dockerfile. The container runs on GKE Autopilot which provides default encryption at rest for persistent volumes and etcd using Google-managed keys. However, no customer-managed KMS keys (CMEK) are configured in the Terraform. The AlloyDB path presumably uses Google-managed encryption by default, but no explicit KMS configuration is present.
- **Gap**: No customer-managed encryption keys. Reliance on Google-managed default encryption. No explicit encryption configuration in IaC for data stores that agents will access.
- **Compensating Controls**:
  - GKE Autopilot provides default encryption at rest (Google-managed)
  - AlloyDB provides default encryption at rest (Google-managed)
- **Remediation Timeline**: 60–90 days
- **Recommendation**: For P0 services handling agent traffic, configure CMEK for GKE persistent volumes and AlloyDB using Cloud KMS. Add KMS key configuration to the Terraform definitions.
- **Evidence**: `Dockerfile` (products.json copied into image), `terraform/main.tf` (no KMS configuration), `kubernetes-manifests/productcatalogservice.yaml` (no volume encryption config)

### OBS-Q1: Distributed Tracing and Structured Logging

- **Severity**: RISK
- **Finding**: OpenTelemetry tracing is implemented: the service initializes an OTLP gRPC trace exporter when `ENABLE_TRACING=1`, uses `AlwaysSample()` sampler, and instruments the gRPC server with `otelgrpc.NewServerHandler()` for automatic trace context propagation. Structured logging uses logrus with JSON formatter, outputting timestamp (RFC3339Nano), severity, and message fields.
- **Gap**: Trace IDs are propagated via OpenTelemetry but are not correlated with log entries — log entries do not include `trace_id`, `span_id`, or `request_id` fields. An agent-initiated request can be traced via OTel but cannot be correlated with application log entries. Tracing is disabled by default (`ENABLE_TRACING` env var must be explicitly set).
- **Compensating Controls**:
  - Enable `ENABLE_TRACING=1` in production Kubernetes manifest
  - Use the GKE logging agent to correlate OTel traces with logs at the cluster level
- **Remediation Timeline**: 30 days
- **Recommendation**: Add trace ID and span ID from the OpenTelemetry context to every logrus log entry using a gRPC interceptor or logrus hook. Enable tracing by default in the Kubernetes manifest.
- **Evidence**: `server.go` (`initTracing` function, `otelgrpc.NewServerHandler()`, `logrus.JSONFormatter`, `ENABLE_TRACING` env var check)

### OBS-Q2: Alerting on Error Rates and Latency

- **Severity**: RISK
- **Finding**: No alerting configuration found anywhere in the repository. The Terraform enables the Cloud Monitoring API (`monitoring.googleapis.com`) and Cloud Trace API (`cloudtrace.googleapis.com`) but defines no alert policies, uptime checks, or SLO-based alerts. No PagerDuty, OpsGenie, or notification channel configuration exists. The Kubernetes manifest includes liveness and readiness probes (gRPC health check) but no alerting on probe failures beyond Kubernetes restart behavior.
- **Gap**: No alerting on error rates, latency, or availability. If the service degrades, agents consuming it will experience failures with no operational team notification.
- **Compensating Controls**:
  - Kubernetes liveness/readiness probes will restart unhealthy pods automatically
  - GKE Autopilot provides basic infrastructure monitoring
- **Remediation Timeline**: 30 days
- **Recommendation**: Create Cloud Monitoring alert policies for: gRPC error rate exceeding threshold, P95 latency exceeding threshold, pod restart count, and availability. Configure notification channels (email, PagerDuty).
- **Evidence**: `terraform/main.tf` (monitoring API enabled, no alert policies), `kubernetes-manifests/productcatalogservice.yaml` (health probes only)

---

## INFOs — Architecture and Design Inputs

### API-Q1: Documented API Interface

- **Severity**: INFO
- **Finding**: The service exposes a well-documented gRPC interface defined in `protos/demo.proto` with 3 RPCs: `ListProducts(Empty) → ListProductsResponse`, `GetProduct(GetProductRequest) → Product`, and `SearchProducts(SearchProductsRequest) → SearchProductsResponse`. This is a documented, strongly-typed interface with clear request/response schemas — not database access, file-based exchange, or UI automation. The generated Go code in `genproto/` provides type-safe client/server stubs.
- **Implication**: The gRPC interface is agent-consumable via gRPC client libraries or a gRPC-to-REST gateway (grpc-gateway). Agent tool definitions can be auto-generated from the proto definition.
- **Recommendation**: Consider deploying `grpc-gateway` or `grpcurl` for agents that prefer REST/JSON over native gRPC.
- **Evidence**: `protos/demo.proto` (ProductCatalogService definition), `genproto/demo_grpc.pb.go` (generated gRPC stubs), `product_catalog.go` (RPC implementations)

### API-Q4: Idempotent Write Operations ⚡

- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: This is a read-only catalog service with no write endpoints. All 3 RPCs (ListProducts, GetProduct, SearchProducts) are read operations. Idempotency is inherently satisfied for all read operations. No write endpoints exist that would require idempotency keys or duplicate detection.
- **Implication**: Read-only agent scope is naturally safe for this service. If write operations (e.g., AddProduct, UpdateProduct) are added in the future, idempotency must be designed in from the start.
- **Recommendation**: If write operations are ever added to this service, require idempotency keys on all write endpoints.
- **Evidence**: `product_catalog.go` (only read RPCs), `protos/demo.proto` (ProductCatalogService has no write RPCs)

### API-Q6: Structured Response Format

- **Severity**: INFO
- **Finding**: gRPC uses Protocol Buffers (protobuf) — a strongly-typed, schema-defined binary serialization format with JSON transcoding capability. Protobuf provides smaller payloads, faster serialization, and type safety compared to JSON. The `protobuf/jsonpb` package is imported for JSON marshaling of the catalog file, indicating JSON compatibility.
- **Implication**: Agents using gRPC client libraries get native protobuf support. For LLM-based agents that prefer text-based formats, a gRPC-to-JSON transcoding proxy (grpc-gateway) can be deployed. The proto definition serves as both the serialization schema and the API documentation.
- **Recommendation**: Deploy grpc-gateway alongside the service if agents require REST/JSON access.
- **Evidence**: `protos/demo.proto` (protobuf schema), `genproto/demo.pb.go` (protobuf serialization), `catalog_loader.go` (`jsonpb.Unmarshal` for JSON parsing)

### API-Q8: Event Emission for State Changes

- **Severity**: INFO
- **Finding**: No event emission, webhooks, or pub/sub integration. The catalog is loaded from a static JSON file or AlloyDB and cached in memory. No state change events are published when the catalog is reloaded (via SIGUSR1). No SNS, Pub/Sub, EventBridge, or Kafka integration.
- **Implication**: Agents cannot subscribe to catalog update events. They must poll the service to detect changes. For a mostly-static product catalog, polling is acceptable. If real-time catalog change notification is needed, an event emission mechanism would be required.
- **Recommendation**: If agents need real-time catalog update notifications, consider publishing events to Cloud Pub/Sub when the catalog is reloaded.
- **Evidence**: `catalog_loader.go` (no event publishing), `server.go` (SIGUSR1 triggers reload but no event)

### API-Q9: Rate Limit Documentation and Headers

- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. No API Gateway throttle settings. No WAF rate rules. No rate limiting middleware. No `X-RateLimit-Remaining` or `Retry-After` headers (gRPC equivalent would be trailing metadata). The service has no rate limit awareness.
- **Implication**: Agents calling this service have no feedback mechanism for self-throttling. Without rate limit headers, agents cannot adapt their request rate dynamically.
- **Recommendation**: When rate limiting is implemented (STATE-Q5), include rate limit information in gRPC trailing metadata (remaining quota, reset time).
- **Evidence**: `server.go` (no rate limit configuration), `product_catalog.go` (no rate limit metadata in responses)

### API-Q10: API Latency Profile

- **Severity**: INFO
- **Finding**: No performance benchmarks or P95 latency data available. The service reads from a local JSON file (expected sub-millisecond) or AlloyDB (expected single-digit milliseconds for simple queries). The `EXTRA_LATENCY` environment variable can inject artificial delay for testing. No APM dashboards, no load test results, no latency SLOs defined.
- **Implication**: Without latency data, agents cannot be configured with appropriate timeout values. The JSON file path should be very fast (in-memory after first load). The AlloyDB path adds network latency that should be characterized.
- **Recommendation**: Run load tests and publish P95 latency for both data paths (JSON file and AlloyDB). Use these numbers to set agent-side gRPC deadlines.
- **Evidence**: `server.go` (`EXTRA_LATENCY` env var), `product_catalog.go` (in-memory catalog read), `README.md` (describes latency injection feature)

### STATE-Q2: Queryable Current State

- **Severity**: INFO
- **Finding**: The service provides three well-implemented query endpoints: `ListProducts` returns the full catalog, `GetProduct` retrieves a single product by ID, and `SearchProducts` performs text search across product names and descriptions. These allow agents to inspect the current catalog state before taking action.
- **Implication**: Agents can effectively query the catalog state. The read-before-act pattern is well-supported for product lookups and searches.
- **Recommendation**: Add pagination to `ListProducts` and `SearchProducts` for larger catalogs.
- **Evidence**: `product_catalog.go` (ListProducts, GetProduct, SearchProducts implementations)

### STATE-Q3: Concurrency Controls

- **Severity**: INFO
- **Finding**: The service uses a `sync.Mutex` (`catalogMutex`) to protect catalog loading operations, preventing concurrent catalog reloads from corrupting the in-memory catalog. The mutex is acquired in `loadCatalog` and released on completion. For a read-only service serving mostly-static data, this is adequate concurrency control.
- **Implication**: Concurrent reads are safe (no lock required for reading the cached catalog). Catalog reloads are serialized via the mutex. No risk of dirty reads or inconsistent state from concurrent agent requests.
- **Recommendation**: The current concurrency model is appropriate for the read-only use case. If write operations are added, consider read-write locks for better read concurrency.
- **Evidence**: `server.go` (`catalogMutex = &sync.Mutex{}`), `catalog_loader.go` (`catalogMutex.Lock()` in `loadCatalog`)

### HITL-Q1: Draft/Pending State

- **Severity**: INFO
- **Finding**: No draft or pending state exists. The service is a read-only catalog with no write operations. There are no status-based workflows, no two-step commit patterns, and no approval endpoints. This is expected and appropriate for a read-only service.
- **Implication**: Draft states are not needed for read-only agent interactions with the catalog. If the service evolves to support catalog management, draft/pending states should be designed in.
- **Recommendation**: No action required for the current read-only use case.
- **Evidence**: `product_catalog.go` (read-only RPCs only)

### HITL-Q2: Configurable Approval Gates

- **Severity**: INFO
- **Finding**: No approval gates or human-in-the-loop mechanisms. The service has no write operations that would benefit from approval workflows. No Step Functions, no approval API endpoints, no configurable operation-level gates.
- **Implication**: Approval gates are not needed for a read-only catalog service. If write operations are added, configurable approval gates should be implemented for high-risk operations (e.g., bulk price changes, product deletion).
- **Recommendation**: No action required for the current read-only use case.
- **Evidence**: `product_catalog.go` (read-only RPCs only)

### DATA-Q1: Sensitive Data Classification

- **Severity**: INFO
- **Finding**: The product catalog contains only public product information: id, name, description, picture URL, price (USD), and categories. No PII, PHI, financial records, or credentials are present in the data. The `products.json` file contains 9 products with non-sensitive data. The AlloyDB path queries the same fields (id, name, description, picture, price, categories). The AlloyDB password is managed via Secret Manager (see AUTH-Q6).
- **Implication**: The product catalog data is non-sensitive and does not require field-level classification or access controls for agent consumption. No regulatory risk from agent access to this data.
- **Recommendation**: Document the data classification as "public/non-sensitive" for the product catalog. If AlloyDB is used for additional data beyond the product catalog, classify those fields separately.
- **Evidence**: `products.json` (9 products with non-sensitive data), `protos/demo.proto` (Product message fields), `catalog_loader.go` (AlloyDB query selects non-sensitive fields)

### DATA-Q7: PII Redaction in Logs

- **Severity**: INFO
- **Finding**: No PII is processed or stored by this service. The product catalog contains only product data (names, descriptions, prices, categories). Log entries contain product IDs and operational messages but no personal information. The AlloyDB password retrieved from Secret Manager is not logged.
- **Implication**: No PII redaction is needed for the current service because no PII flows through it. If the service ever handles user-specific data (e.g., user preferences, browsing history), PII redaction would become necessary.
- **Recommendation**: No action required for the current data model. Add PII detection if the service scope expands to include user data.
- **Evidence**: `products.json` (no PII), `catalog_loader.go` (Secret Manager password not logged), `server.go` (log entries are operational only)

### DATA-Q8: Data Quality Awareness

- **Severity**: INFO
- **Finding**: No data quality metrics, profiling, or completeness monitoring exist. The product catalog is static data loaded from a JSON file or database. No null rate monitoring, no duplicate detection, no data freshness SLAs. The 9 products in `products.json` appear complete (all fields populated), but no automated validation exists.
- **Implication**: Agents consuming catalog data have no signal about data quality or completeness. If product data has missing fields or stale prices, agents will propagate those errors.
- **Recommendation**: Add startup validation that checks for required fields (id, name, price) and logs warnings for incomplete products. Consider adding a catalog health endpoint.
- **Evidence**: `products.json` (all products have populated fields), `catalog_loader.go` (no validation logic)

### DISC-Q2: Semantically Meaningful Field Names

- **Severity**: INFO
- **Finding**: Field names in the proto definition are clear and semantically meaningful: `id`, `name`, `description`, `picture`, `price_usd` (with sub-fields `currency_code`, `units`, `nanos`), `categories`. No legacy abbreviations or opaque codes. The `Money` message type has well-documented fields with comments explaining the nanos representation.
- **Implication**: Agent LLMs can interpret field names directly without requiring a data dictionary. The semantic clarity of the schema reduces the need for additional mapping or documentation.
- **Recommendation**: No action required. The naming convention is exemplary.
- **Evidence**: `protos/demo.proto` (Product and Money message definitions with comments)

### DISC-Q3: Data Catalog / Metadata Layer

- **Severity**: INFO
- **Finding**: No formal data catalog or metadata layer exists. The proto definition (`demo.proto`) serves as an informal schema catalog. No Glue Data Catalog, no DataHub, no Collibra, no API catalog beyond the proto file itself.
- **Implication**: Agent tool builders must reference the proto file directly to understand available data. For a single-service assessment, this is adequate. For a portfolio with many services, a centralized API catalog would accelerate tool definition.
- **Recommendation**: Consider publishing the proto definition to a centralized API catalog (e.g., Backstage, Buf Schema Registry) for discoverability across the microservices portfolio.
- **Evidence**: `protos/demo.proto` (serves as informal schema catalog)

### DISC-Q4: Data Lineage

- **Severity**: INFO
- **Finding**: No data lineage tracking exists. Product data originates from either `products.json` (static file) or AlloyDB (database). No transformation history, no ETL documentation, no source-to-target mappings. The data loading functions are straightforward (JSON parse or SQL query) with no complex transformations.
- **Implication**: For a simple read-only catalog with minimal transformation, lineage is straightforward (source → memory). If the data pipeline becomes more complex (e.g., ETL from multiple sources, price calculations, category enrichment), lineage tracking becomes important for debugging agent-reported data issues.
- **Recommendation**: Document the data flow: `products.json` or `AlloyDB table → loadCatalog → in-memory catalog → gRPC response`. Formalize lineage if the data pipeline grows.
- **Evidence**: `catalog_loader.go` (two data sources, direct load with no transformation)

### OBS-Q3: Business Outcome Metrics

- **Severity**: INFO
- **Finding**: No business outcome metrics are published. No custom Cloud Monitoring metrics, no business KPI tracking, no conversion or satisfaction metrics. The service has only infrastructure-level observability: gRPC health probes, OpenTelemetry traces, and structured logs.
- **Implication**: When agents consume the catalog, there is no way to measure whether agent-retrieved products lead to positive business outcomes (e.g., purchase conversion, recommendation accuracy). Business metrics would be essential for evaluating agent effectiveness.
- **Recommendation**: Publish custom metrics for: catalog query volume by source (agent vs frontend), cache hit rate, catalog load latency, and product retrieval patterns. Correlate with downstream business metrics in the checkout service.
- **Evidence**: `server.go` (health check only), `kubernetes-manifests/productcatalogservice.yaml` (gRPC health probes only)

---

## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: INFO
- **Finding**: The service exposes a documented gRPC interface defined in `protos/demo.proto` with 3 RPCs: `ListProducts`, `GetProduct`, `SearchProducts`. All RPCs have typed request/response schemas using protobuf. Generated Go stubs in `genproto/` provide type-safe client/server implementations. This is a well-defined, machine-consumable interface.
- **Gap**: No gap. The service has a documented, typed API interface.
- **Recommendation**: Consider deploying grpc-gateway for REST/JSON access for agents that prefer HTTP.
- **Evidence**: `protos/demo.proto`, `genproto/demo_grpc.pb.go`, `product_catalog.go`

#### API-Q2: Machine-Readable API Specification
- **Severity**: RISK
- **Finding**: The protobuf definition (`protos/demo.proto`) is a machine-readable specification defining request/response schemas. Generated code is checked in. However, no schema registry, no gRPC server reflection, and no validation that proto and generated code are in sync.
- **Gap**: No schema registry or breaking change detection. gRPC server reflection not enabled.
- **Recommendation**: Enable gRPC server reflection. Add `buf lint` and `buf breaking` to CI.
- **Evidence**: `protos/demo.proto`, `genproto/demo.pb.go`, `genproto.sh`

#### API-Q3: Structured Error Responses
- **Severity**: RISK
- **Finding**: Uses gRPC status codes: `codes.NotFound` for missing products, `codes.Unimplemented` for unsupported methods. No custom error details, no retryable boolean, no error categories. Catalog load failures return empty results instead of errors.
- **Gap**: No rich error model. Agents cannot distinguish retriable from terminal errors without custom logic.
- **Recommendation**: Use gRPC rich error model (`errdetails` package). Propagate catalog load failures as gRPC errors.
- **Evidence**: `product_catalog.go` (status.Errorf, parseCatalog returns empty on error)

#### API-Q4: Idempotent Write Operations ⚡
- **Severity**: INFO
- **Conditional**: agent_scope is "read-only" — evaluated as INFO
- **Finding**: Read-only service with no write endpoints. All 3 RPCs are read operations. Idempotency is inherently satisfied.
- **Gap**: No gap for current read-only scope.
- **Recommendation**: If write operations are added, require idempotency keys from the start.
- **Evidence**: `product_catalog.go`, `protos/demo.proto`

#### API-Q5: API Versioning and Deprecation
- **Severity**: RISK
- **Finding**: gRPC package is `hipstershop` with no version suffix. No API versioning. No deprecation policy. No changelog.
- **Gap**: No versioning strategy. Breaking changes would silently break consumers.
- **Recommendation**: Adopt proto package versioning (e.g., `hipstershop.v1`). Add `buf breaking` to CI.
- **Evidence**: `protos/demo.proto` (package hipstershop)

#### API-Q6: Structured Response Format
- **Severity**: INFO
- **Finding**: gRPC uses Protocol Buffers — strongly-typed, schema-defined binary format with JSON transcoding capability. Ideal for machine consumption.
- **Gap**: No gap. Protobuf is an excellent structured format.
- **Recommendation**: Deploy grpc-gateway for REST/JSON access if needed by agents.
- **Evidence**: `protos/demo.proto`, `genproto/demo.pb.go`, `catalog_loader.go` (jsonpb import)

#### API-Q7: Asynchronous Operation Support
- **Severity**: RISK
- **Finding**: All 3 RPCs are synchronous unary calls. No streaming, async patterns, or long-running operation support. AlloyDB path introduces network latency with no async fallback.
- **Gap**: No async patterns. AlloyDB connection has no timeout or async fallback.
- **Recommendation**: Add gRPC deadlines on server side. Implement cache-aside pattern for AlloyDB reads.
- **Evidence**: `product_catalog.go`, `server.go` (EXTRA_LATENCY)

#### API-Q8: Event Emission for State Changes
- **Severity**: INFO
- **Finding**: No event emission, webhooks, or pub/sub integration. Catalog is loaded from static file or database with no change notifications.
- **Gap**: No event-driven patterns. Agents must poll to detect changes.
- **Recommendation**: Publish events to Cloud Pub/Sub when catalog is reloaded.
- **Evidence**: `catalog_loader.go`, `server.go` (SIGUSR1 reload)

#### API-Q9: Rate Limit Documentation and Headers
- **Severity**: INFO
- **Finding**: No rate limit documentation or headers. No API Gateway, no throttling middleware, no rate limit metadata in gRPC responses.
- **Gap**: Agents have no feedback mechanism for self-throttling.
- **Recommendation**: Include rate limit information in gRPC trailing metadata when rate limiting is implemented.
- **Evidence**: `server.go`, `product_catalog.go`

#### API-Q10: API Latency Profile
- **Severity**: INFO
- **Finding**: No performance benchmarks or P95 latency data. JSON file path expected sub-millisecond. AlloyDB path adds network latency. `EXTRA_LATENCY` env var exists for latency injection testing.
- **Gap**: No latency data for agent timeout configuration.
- **Recommendation**: Run load tests and publish P95 latency for both data paths.
- **Evidence**: `server.go` (EXTRA_LATENCY), `README.md`

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: BLOCKER
- **Finding**: gRPC server initialized with no authentication interceptors, no TLS, no token validation. Uses `insecure.NewCredentials()`. Any caller with network access can invoke all RPCs.
- **Gap**: No authentication mechanism. Cannot identify which agent or caller made a request.
- **Recommendation**: Add gRPC auth interceptor for JWT/API key validation. Enable GKE Workload Identity.
- **Evidence**: `server.go` (grpc.NewServer with no auth), `kubernetes-manifests/productcatalogservice.yaml`

#### AUTH-Q2: Scoped Permissions (Least Privilege)
- **Severity**: RISK
- **Finding**: No permission model. Kubernetes ServiceAccount exists but has no role bindings or IAM annotations. All RPCs accessible to any caller.
- **Gap**: No scoped permissions. Cannot restrict access per endpoint.
- **Recommendation**: Define Istio AuthorizationPolicy rules. Bind ServiceAccount to GCP IAM via Workload Identity.
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml`, `terraform/main.tf`

#### AUTH-Q3: Action-Level Authorization
- **Severity**: RISK
- **Finding**: No authorization checks in service code. All 3 RPCs open to any caller with network access.
- **Gap**: No action-level authorization. Cannot restrict an agent to specific RPCs.
- **Recommendation**: Add gRPC authorization interceptor with method-level policy.
- **Evidence**: `product_catalog.go`

#### AUTH-Q4: Identity Propagation
- **Severity**: RISK
- **Finding**: No token parsing, JWT validation, or user context extraction. gRPC methods do not read identity from context.
- **Gap**: No identity propagation. All requests are anonymous.
- **Recommendation**: Extract caller identity from gRPC metadata/JWT claims in interceptor.
- **Evidence**: `product_catalog.go`, `server.go`

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User
- **Severity**: RISK
- **Finding**: No distinction between caller types. No identity handling exists.
- **Gap**: No agent mode differentiation.
- **Recommendation**: After AUTH-Q1, define two distinct caller identity patterns.
- **Evidence**: `product_catalog.go`, `server.go`

#### AUTH-Q6: Credential Management
- **Severity**: RISK
- **Finding**: AlloyDB code path uses Secret Manager for database password (`getSecretPayload` function). No hardcoded credentials in source. AlloyDB config uses environment variables.
- **Gap**: No credential rotation mechanism visible. No rotation handling in connection pool.
- **Recommendation**: Enable Secret Manager auto-rotation. Move sensitive config to Kubernetes Secrets.
- **Evidence**: `catalog_loader.go` (Secret Manager), `kubernetes-manifests/productcatalogservice.yaml`

#### AUTH-Q7: Immutable Audit Logging ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Structured logging with logrus JSON formatter exists but no audit-specific logging. No caller identity logged per request. No CloudTrail or immutable log storage.
- **Gap**: No audit logging. Cannot determine who made which request.
- **Recommendation**: Add gRPC logging interceptor for caller identity. Configure immutable log storage.
- **Evidence**: `server.go` (logrus JSONFormatter), `terraform/main.tf`

#### AUTH-Q8: Agent Identity Suspension
- **Severity**: RISK
- **Finding**: No identity management exists since there is no authentication. Only way to block a caller is network-level changes.
- **Gap**: Cannot suspend individual agent identities.
- **Recommendation**: After AUTH-Q1, add API key/token revocation mechanism.
- **Evidence**: `server.go`

### 03 — State Management and Transactional Integrity

#### STATE-Q1: Compensation and Rollback ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: Read-only catalog service with no write operations. No saga patterns, compensation logic, or undo endpoints needed for current scope.
- **Gap**: No compensation mechanisms. Cannot support write-enabled agent scenarios.
- **Recommendation**: Maintain read-only agent scope. Design compensation if write ops are added.
- **Evidence**: `product_catalog.go`

#### STATE-Q2: Queryable Current State
- **Severity**: INFO
- **Finding**: Three query endpoints (ListProducts, GetProduct, SearchProducts) allow agents to inspect current catalog state effectively.
- **Gap**: No pagination on ListProducts/SearchProducts. Otherwise well-implemented.
- **Recommendation**: Add pagination for larger catalogs.
- **Evidence**: `product_catalog.go`

#### STATE-Q3: Concurrency Controls
- **Severity**: INFO
- **Finding**: `sync.Mutex` (`catalogMutex`) protects catalog loading operations. Concurrent reads are safe. Adequate for read-only service.
- **Gap**: Coarse-grained locking for catalog refresh. Appropriate for current use case.
- **Recommendation**: Current model is appropriate. Consider read-write locks if write operations are added.
- **Evidence**: `server.go` (catalogMutex), `catalog_loader.go`

#### STATE-Q4: Circuit Breakers and Resilience
- **Severity**: RISK
- **Finding**: No circuit breakers or retry logic for external calls. AlloyDB connection fails immediately with no retry. OTel collector connection has 3s timeout but no retry.
- **Gap**: No resilience patterns for data path. Transient AlloyDB failure causes silent degradation.
- **Recommendation**: Add retry with backoff for AlloyDB. Implement local cache for last known good catalog.
- **Evidence**: `catalog_loader.go`, `server.go` (mustConnGRPC)

#### STATE-Q5: Rate Limiting and Throttling
- **Severity**: RISK
- **Finding**: No rate limiting at any layer. Resource limits in K8s manifest provide natural bounding but no explicit rate limiting.
- **Gap**: No protection against runaway agent loops.
- **Recommendation**: Add gRPC rate limiting interceptor or Istio/Envoy rate limiting.
- **Evidence**: `server.go`, `kubernetes-manifests/productcatalogservice.yaml`

#### STATE-Q6: Blast Radius and Transaction Limits
- **Severity**: RISK
- **Finding**: No configurable transaction limits. ListProducts returns all products without pagination. No per-agent quotas.
- **Gap**: No agent-specific limits on data retrieval volume.
- **Recommendation**: Add pagination. Define per-agent rate limits.
- **Evidence**: `product_catalog.go`, `products.json`

#### STATE-Q7: Infrastructure Capacity for Agent Traffic
- **Severity**: RISK
- **Finding**: No load testing. No HPA. Single replica implied. Resource limits are conservative (200m CPU, 128Mi memory).
- **Gap**: Single replica with no autoscaling. Not tested for agent traffic patterns.
- **Recommendation**: Configure minimum 2 replicas and HPA. Run load tests.
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml`

### 04 — Human-in-the-Loop and Approval Workflows

#### HITL-Q1: Draft/Pending State
- **Severity**: INFO
- **Finding**: No draft/pending state. Read-only service with no write operations. Not needed for current scope.
- **Gap**: No gap for read-only use case.
- **Recommendation**: No action required for current scope.
- **Evidence**: `product_catalog.go`

#### HITL-Q2: Configurable Approval Gates
- **Severity**: INFO
- **Finding**: No approval gates. Read-only service with no operations requiring approval.
- **Gap**: No gap for read-only use case.
- **Recommendation**: No action required for current scope.
- **Evidence**: `product_catalog.go`

#### HITL-Q3: Sandbox/Staging Environment
- **Severity**: RISK
- **Finding**: PR-specific ephemeral deployments exist via CI pipeline. Skaffold supports local dev. No persistent staging with production-equivalent data.
- **Gap**: No persistent staging environment for agent testing.
- **Recommendation**: Create persistent staging environment with production-equivalent data.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `skaffold.yaml`

### 05 — Data Accessibility and Quality

#### DATA-Q1: Sensitive Data Classification
- **Severity**: INFO
- **Finding**: Product catalog contains only non-sensitive public data: product names, descriptions, prices, categories. No PII, PHI, or financial records. AlloyDB password managed via Secret Manager.
- **Gap**: No gap. Data is non-sensitive public product information.
- **Recommendation**: Document data classification as "public/non-sensitive."
- **Evidence**: `products.json`, `protos/demo.proto`, `catalog_loader.go`

#### DATA-Q2: Data Residency and Sovereignty ⚡
- **Severity**: RISK
- **Conditional**: agent_scope is "read-only" — evaluated as RISK
- **Finding**: No data residency requirements documented. GKE region configurable via Terraform (default us-central1). Product data is non-sensitive, not typically subject to residency requirements.
- **Gap**: No data residency controls or documentation.
- **Recommendation**: Document data residency posture. Implement controls if data scope expands.
- **Evidence**: `terraform/variables.tf`, `catalog_loader.go`

#### DATA-Q3: Selective Query Support
- **Severity**: RISK
- **Finding**: GetProduct supports single-item lookup. SearchProducts supports text search. ListProducts returns ALL products with no pagination.
- **Gap**: No pagination, no filtering, no sorting on ListProducts and SearchProducts.
- **Recommendation**: Add pagination parameters to ListProducts and SearchProducts.
- **Evidence**: `product_catalog.go`, `protos/demo.proto`

#### DATA-Q4: System of Record Designations
- **Severity**: RISK
- **Finding**: No system-of-record documentation. Dual source: JSON file or AlloyDB based on environment variable. No conflict resolution.
- **Gap**: No authoritative source designation.
- **Recommendation**: Designate AlloyDB or JSON as authoritative and document it.
- **Evidence**: `catalog_loader.go`

#### DATA-Q5: Reliable Timestamps
- **Severity**: RISK
- **Finding**: No timestamps on product records. Product message has id, name, description, picture, price, categories — no temporal fields.
- **Gap**: No created_at, updated_at, or event_time fields.
- **Recommendation**: Add timestamp fields to Product protobuf message and database schema.
- **Evidence**: `protos/demo.proto`, `products.json`, `catalog_loader.go`

#### DATA-Q6: Data Freshness Signaling
- **Severity**: RISK
- **Finding**: No data freshness indicators in responses. Catalog reload controlled by SIGUSR1/SIGUSR2 signals with no consumer notification.
- **Gap**: Agents cannot determine if data is current, stale, or cached.
- **Recommendation**: Add last_loaded_at timestamp and data source in gRPC response metadata.
- **Evidence**: `product_catalog.go`, `server.go`

#### DATA-Q7: PII Redaction in Logs
- **Severity**: INFO
- **Finding**: No PII processed by this service. Product catalog data only. AlloyDB password not logged.
- **Gap**: No gap. No PII flows through the service.
- **Recommendation**: No action required. Add PII detection if service scope expands.
- **Evidence**: `products.json`, `catalog_loader.go`, `server.go`

#### DATA-Q8: Data Quality Awareness
- **Severity**: INFO
- **Finding**: No data quality metrics or profiling. Static data from JSON/DB. All 9 products in JSON appear complete.
- **Gap**: No automated data quality validation.
- **Recommendation**: Add startup validation for required fields. Consider catalog health endpoint.
- **Evidence**: `products.json`, `catalog_loader.go`

### 06 — Discoverability and Semantic Readiness

#### DISC-Q1: Schema Documentation and Versioning
- **Severity**: RISK
- **Finding**: Proto definition serves as schema documentation. Field numbers provide wire-level compatibility. Generated code checked in. genproto.sh documents regeneration.
- **Gap**: No semantic versioning. No schema registry. Monolithic proto file for all services.
- **Recommendation**: Split proto per service. Adopt buf for schema management.
- **Evidence**: `protos/demo.proto`, `genproto.sh`, `genproto/demo.pb.go`

#### DISC-Q2: Semantically Meaningful Field Names
- **Severity**: INFO
- **Finding**: Field names are clear and semantic: id, name, description, picture, price_usd, categories, currency_code, units, nanos. No legacy abbreviations.
- **Gap**: No gap. Naming convention is exemplary.
- **Recommendation**: No action required.
- **Evidence**: `protos/demo.proto`

#### DISC-Q3: Data Catalog / Metadata Layer
- **Severity**: INFO
- **Finding**: No formal data catalog. Proto definition serves as informal schema catalog.
- **Gap**: No centralized API catalog or metadata layer.
- **Recommendation**: Publish proto to centralized API catalog (e.g., Buf Schema Registry, Backstage).
- **Evidence**: `protos/demo.proto`

#### DISC-Q4: Data Lineage
- **Severity**: INFO
- **Finding**: No data lineage tracking. Data originates from products.json or AlloyDB with no transformation history.
- **Gap**: No formal lineage. Data flow is simple and direct.
- **Recommendation**: Document data flow. Formalize lineage if pipeline grows.
- **Evidence**: `catalog_loader.go`

### 07 — Observability of Target Systems

#### OBS-Q1: Distributed Tracing and Structured Logging
- **Severity**: RISK
- **Finding**: OpenTelemetry tracing implemented with OTLP exporter and gRPC server handler. Logrus JSON formatter provides structured logging. However, trace IDs not correlated with log entries. Tracing disabled by default.
- **Gap**: No trace-log correlation. Tracing requires opt-in.
- **Recommendation**: Add trace/span IDs to log entries. Enable tracing by default.
- **Evidence**: `server.go` (initTracing, otelgrpc, logrus JSONFormatter)

#### OBS-Q2: Alerting on Error Rates and Latency
- **Severity**: RISK
- **Finding**: No alerting configuration. Terraform enables Monitoring API but no alert policies. K8s manifest has health probes only.
- **Gap**: No alerting on error rates, latency, or availability.
- **Recommendation**: Create Cloud Monitoring alert policies for error rate, P95 latency, and availability.
- **Evidence**: `terraform/main.tf`, `kubernetes-manifests/productcatalogservice.yaml`

#### OBS-Q3: Business Outcome Metrics
- **Severity**: INFO
- **Finding**: No business metrics. Infrastructure-level health checks only (gRPC health probes).
- **Gap**: No business outcome measurement.
- **Recommendation**: Publish custom metrics for catalog query volume, cache hit rate, load latency.
- **Evidence**: `server.go`, `kubernetes-manifests/productcatalogservice.yaml`

### 08 — Engineering and Deployment Maturity

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface
- **Severity**: RISK
- **Finding**: Terraform provisions GKE cluster. K8s manifests define deployment. Terraform validation CI exists. However: no drift detection, no terraform plan review in PRs, no K8s manifest policy validation.
- **Gap**: Partial IaC governance. No drift detection. No plan review.
- **Recommendation**: Add terraform plan to PRs. Implement drift detection. Add OPA/Gatekeeper policies.
- **Evidence**: `terraform/main.tf`, `kubernetes-manifests/productcatalogservice.yaml`, `.github/workflows/terraform-validate-ci.yaml`

#### ENG-Q2: CI/CD with API Contract Testing
- **Severity**: RISK
- **Finding**: CI pipeline runs Go unit tests for productcatalogservice. No proto contract testing, no breaking change detection, no consumer-driven contract tests.
- **Gap**: No API contract testing in CI. Breaking proto changes not detected.
- **Recommendation**: Add `buf breaking` to CI pipeline. Implement integration tests.
- **Evidence**: `.github/workflows/ci-pr.yaml`, `product_catalog_test.go`

#### ENG-Q3: Rollback Capability
- **Severity**: RISK
- **Finding**: Skaffold with kubectl apply. No blue/green, no canary, no automated rollback triggers. Manual rollback via `kubectl rollout undo`.
- **Gap**: No automated rollback. Manual intervention required.
- **Recommendation**: Configure canary deployment with Istio traffic splitting. Add automated rollback triggers.
- **Evidence**: `skaffold.yaml`, `cloudbuild.yaml`, `kubernetes-manifests/productcatalogservice.yaml`

#### ENG-Q4: API Test Coverage
- **Severity**: RISK
- **Finding**: 4 unit tests covering GetProduct (found/not found), ListProducts, SearchProducts. Tests run in CI. Uses mock data.
- **Gap**: No edge cases, no error format testing, no AlloyDB integration tests, no load tests.
- **Recommendation**: Add edge case tests, concurrent request tests, AlloyDB failure tests.
- **Evidence**: `product_catalog_test.go`, `.github/workflows/ci-pr.yaml`

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data
- **Severity**: RISK
- **Finding**: Products.json embedded in container image. GKE Autopilot provides default Google-managed encryption. No customer-managed KMS keys configured.
- **Gap**: No CMEK. Reliance on Google-managed defaults.
- **Recommendation**: Configure CMEK for GKE and AlloyDB using Cloud KMS.
- **Evidence**: `Dockerfile`, `terraform/main.tf`

#### ENG-Q6: Cross-Origin and Network Policies
- **Severity**: BLOCKER
- **Finding**: K8s Service is ClusterIP (internal). Network policies exist in `kustomize/components/network-policies/` with deny-all default and per-service allow rules. However, network policies are optional (Skaffold profile, not default deployment). gRPC uses insecure credentials. Istio manifests exist for frontend only.
- **Gap**: Network policies not enforced by default. No TLS on gRPC server. Security is opt-in, not default.
- **Recommendation**: Move network policies to default deployment. Enable Istio mTLS for productcatalogservice.
- **Evidence**: `kubernetes-manifests/productcatalogservice.yaml`, `kustomize/components/network-policies/network-policy-productcatalogservice.yaml`, `skaffold.yaml`, `server.go`

---

## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| `terraform/main.tf` | AUTH-Q1, AUTH-Q2, AUTH-Q7, ENG-Q1, ENG-Q5, OBS-Q2, DATA-Q2 |
| `terraform/variables.tf` | DATA-Q2 |
| `terraform/memorystore.tf` | ENG-Q1 |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| `server.go` | API-Q1, API-Q7, API-Q9, API-Q10, AUTH-Q1, AUTH-Q4, AUTH-Q5, AUTH-Q7, AUTH-Q8, STATE-Q3, STATE-Q4, STATE-Q5, DATA-Q6, DATA-Q7, OBS-Q1, OBS-Q3, ENG-Q6 |
| `product_catalog.go` | API-Q1, API-Q3, API-Q4, API-Q7, AUTH-Q3, AUTH-Q4, AUTH-Q5, STATE-Q1, STATE-Q2, STATE-Q6, DATA-Q3, DATA-Q6, HITL-Q1, HITL-Q2 |
| `catalog_loader.go` | API-Q8, AUTH-Q6, STATE-Q4, DATA-Q1, DATA-Q2, DATA-Q4, DATA-Q5, DATA-Q7, DATA-Q8, DISC-Q4 |
| `product_catalog_test.go` | ENG-Q2, ENG-Q4 |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| `protos/demo.proto` | API-Q1, API-Q2, API-Q4, API-Q5, API-Q6, DATA-Q1, DATA-Q3, DATA-Q5, DISC-Q1, DISC-Q2, DISC-Q3 |
| `genproto/demo.pb.go` | API-Q1, API-Q2, API-Q6, DISC-Q1 |
| `genproto/demo_grpc.pb.go` | API-Q1, API-Q2 |
| `genproto.sh` | API-Q2, DISC-Q1 |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| `.github/workflows/ci-pr.yaml` | ENG-Q2, ENG-Q3, ENG-Q4, HITL-Q3, STATE-Q7 |
| `.github/workflows/ci-main.yaml` | ENG-Q2, ENG-Q4 |
| `.github/workflows/terraform-validate-ci.yaml` | ENG-Q1 |
| `cloudbuild.yaml` | ENG-Q3 |
| `skaffold.yaml` | ENG-Q3, ENG-Q6, HITL-Q3 |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| `Dockerfile` | ENG-Q5 |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| `go.mod` | API-Q6 (protobuf deps), AUTH-Q6 (secretmanager dep), STATE-Q4 (no resilience libs), OBS-Q1 (otel deps) |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| `products.json` | DATA-Q1, DATA-Q3, DATA-Q5, DATA-Q8, STATE-Q6 |
| `kubernetes-manifests/productcatalogservice.yaml` | AUTH-Q1, AUTH-Q2, AUTH-Q6, AUTH-Q7, STATE-Q5, STATE-Q7, OBS-Q2, OBS-Q3, ENG-Q1, ENG-Q3, ENG-Q5, ENG-Q6 |
| `kustomize/components/network-policies/network-policy-productcatalogservice.yaml` | ENG-Q6 |
| `kustomize/components/network-policies/network-policy-deny-all.yaml` | ENG-Q6 |
| `istio-manifests/frontend-gateway.yaml` | ENG-Q6 |
| `istio-manifests/frontend.yaml` | ENG-Q6 |
| `istio-manifests/allow-egress-googleapis.yaml` | ENG-Q6 |
| `README.md` | API-Q10 |
