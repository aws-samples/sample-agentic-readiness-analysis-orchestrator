# ARA Question Bank — Steps 2–9

> **Purpose:** Loaded by the Agentic Readiness Analysis (ARA) TD after Discovery and archetype detection (SKILL.md Steps 1–1.6). This is the authoritative catalog of all 43 questions across the 8 sections, each with its severity, scope-conditional resolution, and surface-flag/archetype calibration. Evaluate every applicable question here against the repository evidence.

---

### Step 2: API Surface and Interface Design (8 questions)

Evaluate the application's API surface — the integration layer that agents will call. APIs are the minimum viable integration surface for agent tools. This section assesses whether the APIs are documented, machine-readable, well-structured, versioned, and operationally ready for autonomous consumption.

When MCP-native integration is the target, the findings here inform what an MCP server wrapping this system will need to expose.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### API-Q1: Documented API Interface — BLOCKER

**Question:** Does the application expose a documented REST, GraphQL, or AsyncAPI interface, or does integration require direct database access, file-based exchange, or UI automation?

**Why it matters:** Agent tools must bind to stable, predictable interfaces. Direct database or file-based integration creates brittle, non-auditable coupling. UI automation (RPA) is fragile and unscalable. An API is the minimum viable integration surface.

**Look for:**
- REST endpoints in code (Express routes, Flask/FastAPI routes, Spring `@RestController`)
- GraphQL schema files
- AsyncAPI specs
- Direct database connection strings in client-facing code
- File-based data exchange patterns
- Selenium/Puppeteer/RPA scripts

---

#### API-Q2: Machine-Readable API Specification — RISK-QUALITY

**Question:** Is there an OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification available and kept current with the implementation?

**Why it matters:** Agent frameworks use machine-readable specs to generate tool definitions automatically. Without one, every integration requires manual tool authoring that drifts from actual behavior. Classified as RISK-QUALITY (not BLOCKER) because GraphQL schemas, Smithy models, and well-documented SDKs serve the same purpose — the real blocker is no machine-readable interface at all (API-Q1).

**Surface-flag calibration:** If `has_http_rpc_surface` is `false`, the system exposes no callable API surface — there is nothing for a machine-readable spec to describe. Record as INFO with the rationale `"No HTTP/RPC surface — machine-readable spec is not applicable."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO. For libraries, API contracts are expressed via package manifests and typed exports (TypeScript declarations, Python type hints, Go interfaces), which DISC-Q1 evaluates — not as OpenAPI specs.

**Look for:**
- OpenAPI/Swagger files (`openapi.yaml`, `openapi.json`, `swagger.yaml`, `swagger.json`)
- AsyncAPI specifications
- GraphQL schema files (`.graphql`, `.gql`)
- Smithy models (`.smithy`)
- Check: Is the spec auto-generated from annotations (preferred) or manually maintained? When was it last updated relative to the last API change?

---

#### API-Q3: Structured Error Responses — RISK-QUALITY

**Question:** Do API responses include structured error codes and machine-readable error bodies — not just HTTP status codes?

**Why it matters:** Agents need to distinguish retriable errors (timeout, rate limit) from terminal errors (invalid input, permission denied). A 500 with no body forces agents to guess.

**Surface-flag calibration:** If `has_http_rpc_surface` is `false`, there are no API responses to structure — record as INFO with the rationale `"No HTTP/RPC surface — structured error responses are not applicable."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO. Libraries communicate failure via typed exceptions, error-return conventions, or Result types — which DISC-Q1 evaluates.

**Look for:**
- Error response structures in code (error code, error message, retryable boolean or category)
- Consistent error response format across endpoints
- Minimum: error code, error message, and a retryable boolean or category

**Cross-reference — input validation:** Input validation and schema enforcement is evaluated as a dedicated question in DATA-Q4. When evaluating API-Q3, note whether validation *error responses* are structured (field name, constraint violated, accepted format) — that evidence feeds both API-Q3 (error structure quality) and DATA-Q4 (whether validation exists at all). See DATA-Q4 for the full evaluation criteria.

---

#### API-Q4: Idempotent Write Operations — BLOCKER ⚡ (Conditional)

**Question:** Are write API endpoints idempotent?

**⚡ Conditional BLOCKER:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **BLOCKER**. Agents retry on failure. LLM non-determinism can cause duplicate tool calls. A non-idempotent write endpoint will duplicate orders, payments, or records on retry. Data integrity risk at machine speed.
- **When `agent_scope` is `"read-only"`:** Evaluate as **INFO**. Read-only agents do not execute write operations, so idempotency is informational only.

**Why it matters:** Agents retry on failure. LLM non-determinism can cause duplicate tool calls. A non-idempotent write endpoint will duplicate orders, payments, or records on retry. Data integrity risk at machine speed.

**Look for:**
- Idempotency key support in write endpoints
- Check: Does POST /orders with the same idempotency key create one record or two?
- Idempotency middleware or decorators
- Unique constraint enforcement on business keys

---

#### API-Q5: Structured Response Format — INFO

**Question:** What is the response format from service APIs? Structured JSON? XML? Binary?

**Why it matters:** LLMs consume text-based formats effectively. Complex XML or binary formats require extra parsing logic. Well-documented JSON APIs can be exposed as agent tools with minimal adaptation.

**Look for:**
- Response serialization in code
- Content-type headers
- Protobuf/Thrift definitions
- XML marshaling
- JSON serialization libraries

---

#### API-Q6: Asynchronous Operation Support — RISK-QUALITY

**Question:** Does the application support async patterns for long-running tasks (job submission, polling endpoint, or webhook callback)?

**Why it matters:** Agents operating synchronously against long-running operations will hit timeout limits and create orphaned processes. Async patterns are required for any operation exceeding 30 seconds.

**Look for:**
- Background job frameworks (Celery, Bull, SQS workers)
- Async/polling patterns
- Job status APIs
- Lambda async invocations
- Step Functions for long processes
- Webhook callback endpoints

---

#### API-Q7: Event Emission for State Changes — INFO

**Question:** Can the system emit events or webhooks for meaningful state changes that agents may need to react to — such as record updates, status transitions, or completion of long-running operations?

**Why it matters:** Request/response agents are reactive. Event-driven patterns unlock proactive agents that respond to real-world changes without polling. Classified as INFO because most agent deployments are request-driven; teams targeting event-reactive agents on time-sensitive use cases should treat this as a stronger signal when scoring.

**Look for:**
- Webhook endpoints
- SNS/EventBridge/SQS integration
- Kafka topics
- CDC pipelines

---

#### API-Q8: Rate Limit Documentation and Headers — INFO

**Question:** Are API rate limits documented, and does the application return rate limit headers (X-RateLimit-Remaining, Retry-After)?

**Why it matters:** Agents call endpoints at machine speed without rate limit awareness. Undocumented limits cause unpredictable failures. Rate limit headers allow agents to self-throttle.

**Look for:**
- API Gateway throttle settings
- WAF rate rules
- Rate limiting middleware
- `X-RateLimit-Remaining` headers in response code
- `aws_api_gateway_usage_plan` in IaC

---

### Step 3: Authentication, Authorization, and Identity (7 questions)

Evaluate the application's authentication, authorization, and identity controls — the security layer that determines who (or what) can call the system and what they can do. Agents cannot use human credentials, so the system must support machine identity, scoped permissions, and immutable audit trails.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### AUTH-Q1: Machine Identity Authentication — BLOCKER

**Question:** Does the application support service account or machine identity authentication (client credentials OAuth 2.0, API key with principal attribution, or mTLS), and can the authenticated principal be attributed in audit logs?

**Why it matters:** Agents cannot use human credentials. The application must distinguish which agent made a call — a generic service account with no attribution is insufficient for audit and forensics. Because ARA is a design-time review, this question evaluates whether the machine-identity *mechanism* exists in code and configuration, not whether it is continuously effective at runtime — and because machine identity sits at the control layer, weak attribution here invalidates every downstream authorization decision (AUTH-Q2, AUTH-Q3, AUTH-Q6).

**Look for:**
- OAuth2 client credentials flow
- API key authentication with principal attribution
- mTLS configuration
- Service account definitions
- Cognito app clients
- Bedrock AgentCore Identity configurations
- API Gateway authorizers
- Check audit logs for agent identity fields

---

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK-SAFETY

**Question:** Does the authorization model support scoped permissions — an agent identity can be granted read-only access to specific resources without inheriting broader privileges?

**Why it matters:** Agents under overly broad permissions create blast radius risk. Without scoped permissions, the system cannot scope down agent access per capability — every agent identity inherits the same broad surface. Least-privilege is critical, though enforcement can happen at the platform layer (API Gateway, IAM policies) if the app itself is coarse-grained.

**Look for:**
- IAM policies with specific actions per resource vs wildcards (`Action: "*"`, `Resource: "*"`)
- Role-per-service vs shared roles
- API Gateway resource policies
- Condition keys in IAM policies

**Evaluation threshold:** The system passes if it supports creating scoped permissions for a caller identity — i.e., the authorization model allows differentiating access levels (not all callers get the same permissions). It does NOT require that every policy in the repo is perfectly scoped. Evidence of wildcard policies on non-production or internal-only roles does not fail this question if production-facing roles demonstrate scope differentiation. Fail if ALL authorization is coarse-grained (single shared role, no mechanism to scope down).

---

#### AUTH-Q3: Action-Level Authorization — RISK-SAFETY

**Question:** Can the application enforce action-level authorization — allowing an agent to read records but not delete them, even within the same resource type?

**Why it matters:** Action-level authorization (ABAC or fine-grained RBAC) is required for agents executing multi-step workflows with mixed read/write operations.

**Look for:**
- ABAC policies
- Fine-grained RBAC definitions
- Permission matrices in code
- Action-level checks in middleware (`canRead`, `canWrite`, `canDelete`)
- API Gateway method-level authorization

---

#### AUTH-Q4: Identity Propagation and Delegation — RISK-SAFETY

**Question:** Does the system support identity propagation through service calls (JWT/OAuth token exchange, on-behalf-of flows), and can it distinguish between an agent acting under its own service identity vs. acting on behalf of a specific human user?

**Why it matters:** Without identity propagation, the system either trusts all internal calls equally or requires each service to re-authenticate — both are problematic. Additionally, an agent acting as itself should have tightly scoped permissions, while an agent acting on behalf of a user should be bounded by that user's permissions. Conflating the two is a common source of privilege escalation. The user is the subject (whose data and permissions apply); the agent is the actor (executing the operation). The system must distinguish both dimensions. This question serves ARA's dual purpose: portfolio telemetry (which systems can carry propagated identity) and use-case-level dependency checking (whether a specific on-behalf-of agent workflow is blocked).

When the target system serves multiple tenants, weak identity propagation compounds with data-layer risks — see DATA-Q2 (data residency) and DATA-Q6 (PII in logs). Treat these as a cluster when planning remediation.

**Archetype calibration:** For `stateless-utility` and `data-gateway` archetypes, downgrade to INFO — stateless services returning public/reference data are not affected by caller identity, and data gateways typically serve as read-only query layers where identity context has minimal security impact.

**Look for:**
- JWT parsing middleware
- OAuth2 on-behalf-of flows
- Token exchange patterns
- Cognito/Okta integration
- User context headers (`X-User-Id`, `Authorization Bearer`) passed through service calls
- Separate IAM roles or API keys for agent-as-self vs agent-on-behalf-of-user
- Different auth flows for service-to-service vs user-delegated calls
- Audit log fields distinguishing the two modes

---

#### AUTH-Q5: Credential Management — RISK-SAFETY

**Question:** Are credentials managed through a secrets management system (AWS Secrets Manager, HashiCorp Vault) with rotation, or are they embedded in code, environment variables, or configuration files?

**Why it matters:** Hardcoded credentials are a security vulnerability — a prompt injection attack or agent bug could leak them. Assess whether secret rotation breaks agent continuity.

**Look for:**
- `aws_secretsmanager_*` in IaC
- Vault client imports
- Hardcoded patterns (`password=`, `secret=`, `api_key=` in code)
- `.env` files committed to git
- Environment variables with credential values in docker-compose or task definitions

---

#### AUTH-Q6: Immutable Audit Logging — BLOCKER ⚡ (Conditional)

**Question:** Does the application log the authenticated principal for every write operation, and is that log immutable and tamper-evident?

**⚡ Conditional BLOCKER:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **BLOCKER**. For regulated data contexts (EU AI Act, HIPAA, SOX), immutable audit trails are a compliance requirement. Write-enabled agents must have full audit attribution.
- **When `agent_scope` is `"read-only"`:** Evaluate as **RISK-SAFETY**. Audit logging is still important for read-only agents but is not a deployment blocker.

**Why it matters:** Audit trails must identify whether an action was taken by a human or an agent, and which specific agent instance. Without immutable logs, you cannot prove compliance or conduct forensics.

**Surface-flag calibration:** The conditional above determines severity only when the system has an agent-invocable surface. If the repo was classified as `dev-library-application` via Step 1.5, or if `has_auth_surface` is `false` AND `has_write_operations` is `false`, record as INFO with the rationale `"System does not execute agent-invoked write operations — audit logging is a consumer responsibility. The library/utility is called by applications that own the audit context."`

**Look for:**
- `aws_cloudtrail` in IaC
- CloudTrail log file validation enabled
- S3 bucket with object lock for logs
- CloudWatch log retention policies
- Immutable log storage configuration

---

#### AUTH-Q7: Agent Identity Suspension — RISK-SAFETY

**Question:** Can individual agent identities be suspended or revoked immediately if anomalous behavior is detected, without taking down the broader platform?

**Why it matters:** The ability to isolate a misbehaving agent without disrupting other agents or users is a fundamental operational requirement.

**Surface-flag calibration:** If the repo was classified as `dev-library-application` via Step 1.5, or if `has_auth_surface` is `false`, record as INFO with the rationale `"System does not issue or enforce agent identities — suspension is a consumer responsibility. Libraries and utilities are invoked by applications that own identity lifecycle."`

**Look for:**
- API key revocation endpoints
- IAM role deactivation procedures
- Service account disable mechanisms
- Cognito user pool user disable
- API Gateway API key deletion


### Step 4: State Management and Transactional Integrity (7 questions)

Evaluate the application's state management and transactional integrity — the controls that ensure data consistency, safe concurrent access, and resilience when agents execute multi-step workflows. Agents retry on failure, operate concurrently, and call endpoints at machine speed — the system must handle all of this safely.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### STATE-Q1: Compensation and Rollback — BLOCKER ⚡ (Conditional)

**Question:** Does the application support compensation or rollback for multi-step operations that fail mid-sequence?

**⚡ Conditional BLOCKER:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **BLOCKER**. Agents executing write-enabled multi-step workflows may succeed on steps 1–4 and fail on step 5. Without rollback or compensation logic, the application is left in a partial state.
- **When `agent_scope` is `"read-only"`:** Evaluate as **RISK-SAFETY**. Read-only agents do not execute write workflows, but compensation capability is still relevant for system maturity.

**Why it matters:** Agents executing a 5-step workflow may succeed on steps 1–4 and fail on step 5. Without rollback or compensation logic, the application is left in a partial state.

**Surface-flag calibration:** If `has_write_operations` is `false` AND `has_http_rpc_surface` is `false`, the system has no write path that would need compensation — record as INFO with the rationale `"System exposes no write operations — compensation logic is not applicable."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO. The conditional BLOCKER severity above applies only when the system actually has multi-step write workflows.

**Archetype calibration:** For `stateless-utility` archetype, record as INFO — stateless utilities have no multi-step write sequences.

**Look for:**
- Saga pattern
- Two-phase commit
- Explicit undo endpoints
- Compensating transactions
- Step Functions with error handling and rollback states

---

#### STATE-Q2: Queryable Current State — RISK-QUALITY

**Question:** Does the application expose its current state in a queryable form that an agent can inspect before taking action?

**Why it matters:** Agents need to read current state before deciding next steps. Write-only or event-only interfaces force agents to maintain external state, introducing synchronization risk.

**Look for:**
- GET endpoints for resource state
- Status query APIs
- Read-before-write patterns in code
- State machine status fields in database schemas

---

#### STATE-Q3: Concurrency Controls — RISK-SAFETY ⚡ (Scope-Calibrated)

**Question:** Does the application support optimistic locking or concurrency controls to prevent race conditions when multiple agent instances operate simultaneously?

**⚡ Scope-Calibrated:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **RISK**. Multiple write-enabled agent instances may attempt concurrent writes. Without concurrency controls, data integrity is at risk.
- **When `agent_scope` is `"read-only"`:** Evaluate as **INFO**. Read-only agents do not perform writes, so concurrency controls for write operations are informational only — relevant for future scope expansion planning.

**Why it matters:** Multiple agent instances may attempt concurrent writes. Without concurrency controls (optimistic locking, ETags, version fields), data integrity is at risk.

**Look for:**
- Optimistic locking (version fields, ETags, `If-Match` headers)
- Pessimistic locking (`SELECT FOR UPDATE`)
- DynamoDB conditional writes
- Conflict resolution logic

---

#### STATE-Q4: Circuit Breakers and Resilience — RISK-SAFETY

**Question:** Does the target system implement circuit breakers, retry logic, and timeout configurations for its own external dependency calls?

**Why it matters:** When an agent calls the target system, that request may trigger cascading calls to the system's own dependencies. Circuit breakers prevent the target system from becoming a bottleneck that cascades failures back to the agent.

**Look for:**
- Resilience4j, Polly, retry decorators
- Exponential backoff
- `@CircuitBreaker` annotations
- Timeout configurations on HTTP clients

---

#### STATE-Q5: Rate Limiting and Throttling — RISK-SAFETY

**Question:** Are rate limits enforced at the API layer to prevent runaway agent loops from overwhelming the application?

**Why it matters:** A runaway agent loop can DDoS your own services at machine speed. Rate limiting prevents agent bugs from taking down production.

**Surface-flag calibration:** If `has_http_rpc_surface` is `false`, there is no API layer to enforce rate limits at — record as INFO with the rationale `"System exposes no HTTP/RPC surface — API-layer rate limiting is not applicable."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO. Libraries invoked by consuming applications inherit the consumer's rate limiting, not their own.

**Archetype calibration:** For `stateless-utility` archetype without a persistent API surface, record as INFO.

**Look for:**
- API Gateway throttling config
- WAF rate rules
- Application-level rate limiting middleware (`express-rate-limit`, `django-ratelimit`)
- `aws_api_gateway_usage_plan` in IaC

---

#### STATE-Q6: Blast Radius and Transaction Limits — RISK-SAFETY ⚡ (Scope-Calibrated)

**Question:** Can the system enforce configurable limits on agent-initiated actions — such as maximum records modified per run, maximum spend per hour, or maximum delete operations per session — independently of general rate limits?

**⚡ Scope-Calibrated:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **RISK**. Write-enabled agents can execute correct-but-catastrophic logic at machine speed. Transaction limits define the maximum blast radius of an agent error.
- **When `agent_scope` is `"read-only"`:** Evaluate as **INFO**. Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only — relevant for future scope expansion planning.

**Why it matters:** Rate limits (STATE-Q5) protect the system from traffic overload. Transaction limits protect the business from the consequences of an agent executing correct-but-catastrophic logic — deleting 10,000 records instead of 100, or issuing $50,000 in refunds in a loop. These limits define the maximum blast radius of an agent error.

**Look for:**
- Configurable transaction limits per agent identity
- Examples: `max_refunds_per_hour=50`, `max_records_per_bulk_operation=500`, `max_spend_per_session=$1000`
- Configurable per agent identity, not just per API endpoint

**Evaluation threshold:** This question evaluates whether the system can limit the *business impact* of agent operations beyond API-layer rate limiting (STATE-Q5). Pass if ANY of the following exist: (a) configurable per-caller business transaction limits, (b) bulk operation size caps (e.g., batch delete limited to N records), (c) spend/cost thresholds per session or caller identity. These need not be agent-specific — general per-caller business limits satisfy this question. Fail if the only protection is API-level throttling (requests/second) with no business-domain caps on operation scope.

---

#### STATE-Q7: Graceful Degradation Signaling — RISK-QUALITY

**Question:** Does the system signal degraded mode to callers via machine-readable indicators — so an agent can detect when it is receiving stale, partial, or fallback responses rather than authoritative data?

**Why it matters:** Agents making autonomous decisions on degraded data produce incorrect outcomes at machine speed. If the system fails over to a stale cache, returns partial results from a degraded dependency, or operates in read-only mode, agents need a machine-readable signal to adjust behavior (e.g., defer decisions, request human review, retry later). Without this, agents treat degraded responses as authoritative.

**Look for:**
- Health endpoints returning granular states (healthy / degraded / read-only / partial)
- `X-Degraded: true` or `X-Data-Freshness: stale` response headers
- `Retry-After` headers on 503 responses
- Circuit breaker configs with fallback responses that include degradation metadata
- `Cache-Control` headers with `stale-while-revalidate` or `must-revalidate`
- Response envelope fields like `{ "data_status": "cached", "cached_at": "..." }`
- Feature flag states exposed in response metadata


### Step 5: Human-in-the-Loop and Approval Workflows (3 questions)

Evaluate whether the application supports human oversight for high-stakes agent operations. Agents should not commit irreversible actions autonomously for high-risk operations — draft states, approval gates, and sandbox environments provide defense in depth.

ARA measures whether a target system can *support* human-in-the-loop patterns, not whether HITL is mandatory. HITL is a valuable safety mechanism for high-stakes operations and a confidence-building step during initial agent deployments.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### HITL-Q1: Draft/Pending State — RISK-SAFETY ⚡ (Scope-Calibrated)

**Question:** Does the application have the concept of a pending or draft state that an agent can write to before a human approves and commits?

**⚡ Scope-Calibrated:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **RISK**. Write-enabled agents should not commit irreversible actions autonomously for high-stakes operations. Draft states let agents propose and humans confirm.
- **When `agent_scope` is `"read-only"`:** Evaluate as **INFO**. Read-only agents do not make state changes, so draft/pending states are informational only — relevant for future scope expansion planning.

**Why it matters:** Agents should not commit irreversible actions autonomously for high-stakes operations. Draft states let agents propose and humans confirm. ARA measures whether the target system can *support* human-in-the-loop patterns, not whether HITL is mandatory — HITL is a valuable safety mechanism for high-stakes operations and a confidence-building step during initial agent deployments.

**Look for:**
- Draft/pending status fields in database schemas
- Approval workflow endpoints
- Two-step commit patterns (create-then-confirm)
- Status-based state machines

**Evaluation threshold:** Pass if the system has ANY mechanism where a state change can be proposed without being immediately committed — allowing a human (or supervisory process) to review before finalization. This includes: status enums with PENDING/DRAFT/PROPOSED states, two-step APIs (create-then-confirm), or explicit approval workflow endpoints. Pre-existing business workflow states count IF they can be repurposed for agent-initiated proposals (e.g., an order with status=PENDING_REVIEW). Fail only if all write operations are immediately committed with no reviewable intermediate state.

---

#### HITL-Q2: Configurable Approval Gates — RISK-SAFETY ⚡ (Scope-Calibrated)

**Question:** Can specific operations be configured to require a human approval step before the application executes them — configurable by operation type?

**⚡ Scope-Calibrated:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **RISK**. Write-enabled agents executing high-risk operations benefit from human-in-the-loop approval at the application layer as defense in depth.
- **When `agent_scope` is `"read-only"`:** Evaluate as **INFO**. Read-only agents do not execute write operations, so approval gates are informational only — relevant for future scope expansion planning.

**Why it matters:** High-risk actions benefit from human-in-the-loop approval at the application layer as defense in depth, even when orchestration-layer gates exist.

**Look for:**
- Approval API endpoints
- Status-based workflows requiring explicit confirmation
- Configurable operation-level flags
- Step Functions with human approval tasks (`waitForTaskToken`)

---

#### HITL-Q3: Sandbox/Staging Environment — RISK-QUALITY

**Question:** Is there a sandbox or staging environment with production-equivalent data shape that agents can use for testing without risk to live systems?

**Why it matters:** Agents must be testable against realistic conditions before production promotion. Without a staging environment, the first time you discover an agent bug is in production.

**Surface-flag calibration:** If the repo was classified as `dev-library-application` via Step 1.5, or if `has_http_rpc_surface` is `false` AND `has_persistent_data_store` is `false`, record as INFO. Libraries, CLIs, and scaffolds do not own staging environments — their consumers do. Requiring a library to maintain its own staging is a category error.

**Look for:**
- Separate environment configurations (staging, sandbox)
- Docker-compose for local testing
- Seed data scripts
- Synthetic data generators
- Environment-specific IaC


### Step 6: Data Accessibility and Quality (7 questions)

Evaluate the data layer that agents will access — classification, residency, query capabilities, quality, and privacy controls. Agents process data at machine speed, so unclassified sensitive data, unbounded queries, and PII leakage into logs create regulatory and operational risk at scale.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### DATA-Q1: Sensitive Data Classification — BLOCKER ⚡ (Conditional, Tiered)

**Question:** Does this system store, process, or transmit sensitive data (PII, PHI, financial records, credentials), and if so, are agent-facing API responses scoped to exclude sensitive fields that the agent has no business retrieving?

**Why it matters:** Unscoped data access is a regulatory and reputational risk. The critical question is not whether a formal classification schema exists (most applications do not have one), but whether agent-facing APIs actually filter out sensitive fields. An agent calling `GET /users` should not receive password hashes, and an agent reading order history should not receive full credit card numbers. Access control differentiation (different scopes for sensitive vs non-sensitive) provides the second layer. Formal classification metadata is aspirational but not a deployment gate — most real-world applications (including well-engineered ones) lack field-level classification schemas yet still protect data correctly through API-level filtering.

**Two-stage evaluation:**

**Stage A — Scope gate: does this system handle sensitive data?**

Answer Yes if any of the following is true:
- `has_persistent_data_store` is `true` AND the stored data includes user-specific fields (user_id, email, phone, address, account details), health or medical records, financial instruments (cards, accounts, balances, transactions), or credentials (passwords, tokens, API keys persisted beyond their request lifecycle)
- `has_logging_of_user_data` is `true` AND logs capture request/response bodies that may contain user-submitted PII
- The system's stated purpose involves regulated data domains (healthcare/FHIR, payments/PCI, identity/IAM, telecom CPNI, finance)

Answer No if the system is clearly not a data-handling target. Representative No cases:
- Build tools and compilers (webpack, gulp, rollup) that read source files but never hold user data
- CLI utilities that invoke remote services without persisting user input (aws-cli wrappers, deployment tools)
- Pure computation libraries (date/time, math, formatting) with no persistence
- SDK mocks and test doubles
- Frontend scaffolds and starter templates with no backend
- Progress bars and instrumentation libraries that transmit only user-provided label strings

**If Stage A = No:** Record the question as INFO with the rationale `"Not a data-handling target — no PII/PHI/financial/credential data is stored, processed, or logged."` Skip Stage B entirely. Do not flag absence of classification controls as a finding — this is expected for non-data-handling systems.

**If Stage A = Yes:** Proceed to Stage B.

**Archetype calibration:** For `stateless-utility` archetype (regardless of Stage A result): record as INFO. Stateless utilities operate on transient or public/reference data by definition; if they appear to handle sensitive data, the archetype classification should be revisited — recommend reclassifying before flagging DATA-Q1.

**Dev-library-application override:** If the repo was classified as `dev-library-application` via the Step 1.5 override, skip directly to INFO without evaluating Stage A or Stage B. Libraries, CLIs, and scaffolds do not own the data that consuming applications store.

**Stage B — Tiered evaluation (only if Stage A = Yes):**

Evaluate three layers of data protection for agent-facing access. Each layer has independent severity; the overall DATA-Q1 severity is the highest severity that fires.

**B1: Agent-facing API response scoping — BLOCKER (conditional on `agent_scope`)**

Does the application exclude sensitive fields from API responses that an agent would consume? Look for:
- Password/secret fields excluded from serialization (e.g., `@JsonIgnore`, `exclude_fields`, `hidden` attributes, `write_only=True` in serializers)
- Different response DTOs for internal vs external/agent consumers
- GraphQL field-level authorization or field filtering
- Explicit `select` projections in API handlers that omit sensitive columns
- Sensitive data returned ONLY via dedicated, separately-authorized endpoints (not mixed into general-purpose list/detail responses)

Severity logic for B1:
- If `agent_scope` is `write-enabled` AND sensitive fields are returned in general API responses → **BLOCKER**
- If `agent_scope` is `read-only` AND sensitive fields are returned in general API responses → **RISK-SAFETY**
- If sensitive fields are properly excluded from API responses OR only accessible via separately-scoped endpoints → B1 contributes no finding (CLEAR)

**B2: Access control differentiation — RISK-SAFETY**

Do access controls distinguish between sensitive and non-sensitive data access? Look for:
- OAuth scopes that separate data domains (e.g., `read:profile` vs `read:payment`)
- Role-based access with granularity below "full admin vs no access"
- API key permissions that limit which endpoints/fields are accessible
- Row-level or column-level security in the database access layer

Severity logic for B2:
- If no differentiation exists (a single permission grants access to everything sensitive) → **RISK-SAFETY**
- If differentiation exists → B2 contributes no finding (CLEAR)

**B3: Formal classification metadata — INFO**

Does the system have explicit, machine-readable data classification? Look for:
- Data classification tags in IaC (S3 bucket tags, DynamoDB table tags with sensitivity labels)
- Field-level sensitivity annotations in code (decorators, attributes)
- PII detection tooling integrated (Macie, Presidio)
- Data catalog entries with classification levels
- Documented classification policies

Severity logic for B3:
- If absent → **INFO** (aspirational, not a deployment gate)
- If present → Acknowledge as mature practice; contributes no finding

**Overall DATA-Q1 severity:**
- If B1 fires as BLOCKER → DATA-Q1 = BLOCKER
- Else if B1 fires as RISK-SAFETY or B2 fires → DATA-Q1 = RISK-SAFETY
- Else if only B3 is absent → DATA-Q1 = INFO
- If all three are clear → DATA-Q1 = no finding

**Look for (Stage B):**
- B1 indicators: `@JsonIgnore`, `serialize: false`, `hidden_fields`, `write_only=True`, password exclusion in serializers, separate DTOs for API responses, field-level `@Authorize` in GraphQL, explicit column `select()` in query builders
- B2 indicators: OAuth scope definitions with data-domain granularity, RBAC with more than two roles, API key permission matrices, row-level security policies
- B3 indicators: Classification tags in IaC, field decorators (`@PII`, `@Sensitive`, `@Classified`), Macie/Presidio integration, data catalog references

---

#### DATA-Q2: Data Residency and Sovereignty — BLOCKER ⚡ (Conditional)

**Question:** Is the data subject to residency or sovereignty requirements that would restrict an agent from transmitting it to an LLM provider in a different region or jurisdiction?

**⚡ Conditional BLOCKER:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **BLOCKER**. For regulated data (GDPR, LGPD, HIPAA, sector-specific), an agent sending regulated data to an LLM endpoint in another region may create a legal violation.
- **When `agent_scope` is `"read-only"`:** Evaluate as **RISK-SAFETY**. Data residency is still relevant for read-only agents but the risk profile is lower when no data modification occurs.

**Why it matters:** An agent sending regulated data to an LLM endpoint in another region may create a legal violation. The data residency constraints are properties of the data the system holds.

**Surface-flag calibration:** If `has_persistent_data_store` is `false` AND `has_logging_of_user_data` is `false`, the system holds no data subject to residency constraints — record as INFO with the rationale `"No persistent data store and no user-data logging — residency requirements do not apply."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO. The conditional BLOCKER severity above applies only when at least one of those surface flags is `true`.

**Archetype calibration:** For `stateless-utility` archetype, record as INFO — stateless utilities handle transient or public/reference data by archetype definition.

**Look for:**
- Data residency requirements in documentation
- GDPR/LGPD compliance references
- Region-specific data storage configurations
- Cross-region replication settings
- Data sovereignty policies

---

#### DATA-Q3: Selective Query Support — RISK-QUALITY

**Question:** Can data be queried with filters, pagination, and sorting that limit result set size to what an agent actually needs?

**Why it matters:** Agents retrieving unbounded result sets exhaust LLM context windows and increase cost.

**Look for:**
- Pagination parameters in API endpoints (`limit`, `offset`, `cursor`)
- Filter query parameters
- Sorting options
- GraphQL field selection
- Result size limits in API documentation

---

#### DATA-Q4: Input Validation and Schema Enforcement — RISK-QUALITY

**Question:** Does the system validate and reject malformed inputs at the API boundary with structured error responses that identify which field failed and why?

**Why it matters:** LLMs constructing API calls produce malformed payloads — partial JSON, special characters, oversized strings, out-of-range values, or injection-like fragments. Target systems that accept garbage inputs silently corrupt state. Systems that crash on unexpected input create cascading failures. Systems that return generic 400 errors without field-level detail force agents into blind retry loops. The target system must validate inputs and return structured rejection signals that enable agents to self-correct.

**Look for:**
- Request validation libraries (joi, zod, yup, pydantic, javax.validation, class-validator, marshmallow)
- OpenAPI request body schema validation middleware
- API Gateway request validators
- Parameterized queries (protection against injection)
- Input sanitization middleware
- Request size limits (`max_body_size`, payload limits)
- Type-safe request parsing (TypeScript interfaces, Rust serde, Go struct tags)
- Structured validation error responses with field-level detail (e.g., `{ "errors": [{ "field": "email", "constraint": "format", "message": "..." }] }`)

**Evaluation threshold:** Pass if the system has ANY systematic input validation at the API boundary — either framework-level (validation annotations, middleware) or explicit (manual checks with structured error responses). Presence of parameterized queries alone is insufficient (that prevents injection but doesn't validate business rules). Fail if endpoints accept arbitrary input shapes without validation, or if validation errors return unstructured 400/500 responses with no field identification.

---

#### DATA-Q5: Temporal Metadata and Freshness — RISK-QUALITY

**Question:** Does the data include reliable timestamps (creation, last update, source event time) with timezone normalization, and can the system signal whether data returned to an agent is current, stale, cached, or eventually consistent?

**Why it matters:** Agents performing time-sensitive reasoning depend on accurate temporal data. Missing timestamps cause silent errors. If the system cannot signal that data is cached or eventually consistent, the agent has no way to know whether it is reasoning on the current state. Both concerns — temporal accuracy and freshness signaling — serve the same purpose: ensuring agents reason on trustworthy temporal data.

**Archetype calibration:** For `stateless-utility` archetypes, downgrade to INFO — stateless services with static/reference data have fixed temporal characteristics that don't change at runtime.

**Look for:**
- `created_at`, `updated_at`, `event_time` fields in database schemas
- Timezone handling (UTC storage)
- Timestamp format consistency
- `Cache-Control` headers
- `X-Data-Age` or `last_refreshed` headers
- `consistency_level` field (strong / eventual / cached)
- NTP synchronization configuration

---

#### DATA-Q6: PII Redaction in Logs — RISK-SAFETY

**Question:** Is PII redacted from logs, error messages, and observability data?

**Why it matters:** Agents process customer PII. If PII leaks into logs or LLM prompt/response pairs, it becomes a compliance violation.

**Surface-flag calibration:** If `has_logging_of_user_data` is `false` AND `has_persistent_data_store` is `false`, the system has no pipeline where user PII could enter logs — record as INFO with the rationale `"System does not log user data and holds no user data — PII-in-logs risk is not applicable."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO. Libraries and utilities whose only logging is internal diagnostic output (no user-submitted content) fall in the INFO bucket.

**Archetype calibration:** For `stateless-utility` archetype, record as INFO — stateless utilities do not handle user PII.

**Look for:**
- Log scrubbing middleware
- PII masking libraries
- CloudWatch log filters
- Amazon Macie integration
- Regex patterns for PII in logging utilities

---

#### DATA-Q7: Data Quality Awareness — INFO

**Question:** Is there a known data quality score or completeness metric for this dataset?

**Why it matters:** Agents acting on incomplete or stale data propagate errors faster than human workflows. Planning input, not a deployment blocker.

**Look for:**
- Data quality dashboards
- Data profiling reports
- Null rate monitoring
- Duplicate detection logic
- Data freshness SLAs
- Data quality metrics in observability


### Step 7: Discoverability and Semantic Readiness (3 questions)

Evaluate whether the system's data and APIs are discoverable and semantically meaningful — can an agent (or the team building agent tools) understand what data exists, what it means, and where it came from? This section accelerates tool definition and improves agent reasoning quality.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### DISC-Q1: Schema Versioning and API Contracts — RISK-QUALITY

**Question:** Are data schemas and API contracts documented, versioned, and accessible — with breaking change detection in CI?

**Why it matters:** Agents need to understand data structures, and agent tool schemas break silently when APIs change without notice. Schema changes without versioning break agent queries silently. Every breaking change requires updating tool definitions and revalidating agent behavior. This question covers both schema documentation (the discoverability concern) and API versioning (the stability concern) because they serve the same purpose: ensuring agents can reliably bind to and consume the system's interfaces.

**Look for:**
- JSON Schema files, Avro/Protobuf schemas
- Database migration files
- Schema registry
- OpenAPI schema definitions
- `/v1/`, `/v2/` URL patterns or versioned proto packages
- `Accept-Version` headers
- Changelog files, deprecation notices
- Breaking change detection tools (`buf breaking`, OpenAPI diff)
- Consumer-driven contract tests (Pact)

---

#### DISC-Q2: Semantically Meaningful Field Names — INFO

**Question:** Are field names and identifiers human-readable and semantically meaningful, or are they legacy codes requiring a data dictionary?

**Why it matters:** Agents using LLM-based reasoning need interpretable field names. `CUST_TYP_CD` requires a lookup. `CustomerTypeCode` does not.

**Look for:**
- Field naming conventions in database schemas and API responses
- Legacy abbreviations (`CUST_TYP_CD` vs `CustomerTypeCode`)
- Data dictionary files
- Naming convention documentation

---

#### DISC-Q3: Data Catalog / Metadata Layer — INFO

**Question:** Is there a data catalog or metadata layer describing what data the target system holds and what it means semantically?

**Why it matters:** Accelerates tool definition when building agent tools against this system.

**Look for:**
- AWS Glue Data Catalog
- Collibra, Alation, DataHub
- Metadata files
- Data dictionaries
- Schema documentation
- API catalogs

---

### Step 8: Observability of Target Systems (3 questions)

Evaluate the observability of the target systems that agents will call — distributed tracing, alerting, and business outcome metrics. When an agent-initiated request fails, the target system's observability determines whether you can diagnose the problem or are flying blind.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK-QUALITY

**Question:** Does the application support distributed tracing (X-Ray, OpenTelemetry) with trace ID propagation, and are logs structured (JSON) with correlation IDs linking all entries for a single request?

**Why it matters:** These two controls serve the same diagnostic purpose — reconstructing what happened inside the target system when an agent-initiated request fails. Both must be present to make agent-initiated failures debuggable.

**Surface-flag calibration:** If the repo was classified as `dev-library-application` via Step 1.5, or if `has_http_rpc_surface` is `false` AND there is no agent-initiated request path to trace, record as INFO with the rationale `"Library/utility — tracing and correlation are consumer concerns. The library's obligation is to propagate trace context if provided, which DISC-Q1 evaluates."` Libraries that ship OpenTelemetry hooks or accept a logger instance satisfy the instrumentation concern without owning the trace pipeline.

**Look for:**
- OpenTelemetry SDK
- X-Ray instrumentation
- `traceparent` header propagation
- JSON logs
- `request_id` or `correlation_id` field

---

#### OBS-Q2: Alerting on Error Rates and Latency — RISK-QUALITY

**Question:** Are there alerting thresholds configured for error rates and latency on the APIs agents will consume?

**Why it matters:** Target system degradation is felt immediately by agents. Alerting lets you detect problems before agents start cascading failures.

**Surface-flag calibration:** If the repo was classified as `dev-library-application` via Step 1.5, or if `has_http_rpc_surface` is `false`, record as INFO with the rationale `"Library/utility — alerting on error rates and latency is a consumer concern. Libraries expose error and timing signals via return values, exceptions, or structured metrics; consumers decide the alert thresholds."`

**Look for:**
- CloudWatch alarms on error rates and latency
- Anomaly detection configuration
- PagerDuty/OpsGenie integration
- Composite alarms
- SLO-based alerting

---

#### OBS-Q3: Business Outcome Metrics — INFO

**Question:** Are custom metrics published for business outcomes, not just infrastructure metrics?

**Why it matters:** When agents consume the system, business metrics become the primary signal for whether agent interactions produce good outcomes.

**Look for:**
- `cloudwatch.put_metric_data` for business events
- Custom dashboards tracking resolution rates, conversion, satisfaction
- Business KPI alarms


### Step 9: Engineering and Deployment Maturity (5 questions)

Evaluate the engineering and deployment maturity of the target system — infrastructure governance, CI/CD with contract testing, rollback capability, test coverage, encryption, and network policies. These controls determine whether the system can be safely and reliably operated as an agent integration surface.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK-QUALITY

**Question:** Is the infrastructure exposing the target system to agents — API gateways, IAM roles, secrets, network configurations — defined as code, subject to peer review before changes, and monitored for drift?

**Why it matters:** The integration surface is a high-value attack surface. All three controls — IaC definition, change review, and drift detection — must be present together for this surface to be trustworthy.

**Surface-flag calibration:** If the repo was classified as `dev-library-application` via Step 1.5, or if `has_http_rpc_surface` is `false` AND `has_auth_surface` is `false`, record as INFO. Libraries, CLIs, and formatters do not own the IaC for API gateways, IAM roles, or networking — their consumers do. The library's engineering governance is its own build/release pipeline, which ENG-Q2/Q3 cover.

**Look for:**
- Sub-checks: (1) Integration surface defined as IaC? (2) Changes subject to automated plan review + peer review? (3) Drift detection active?
- Terraform, CloudFormation, or CDK definitions for API Gateway, IAM, secrets, networking
- PR/CR review requirements on IaC changes
- AWS Config rules or drift detection configuration

---

#### ENG-Q2: CI/CD with API Contract Testing — RISK-QUALITY

**Question:** Does the target system have a CI/CD pipeline that includes automated testing of agent-facing APIs and the ability to detect API-breaking changes before production?

**Why it matters:** The agentic concern is not "does CI/CD exist" but "can API contract changes be caught before agents are affected."

**Surface-flag calibration:** If `has_http_rpc_surface` is `false`, there are no APIs to contract-test — record as INFO with the rationale `"No HTTP/RPC surface — API contract testing is not applicable. Library contract stability is evaluated by DISC-Q1 (schema/typed-export versioning)."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO — library build pipelines validate package contracts (semver, typed exports), not API contracts.

**Look for:**
- API contract tests in CI pipeline
- Consumer-driven contract testing (Pact)
- OpenAPI spec validation in build
- Schema comparison tools
- Breaking change detection

---

#### ENG-Q3: Rollback Capability — RISK-QUALITY

**Question:** Can the target system's deployment be rolled back to the previous known-good state if a change breaks agent-facing APIs? (Target: within 15–30 minutes.)

**Why it matters:** A broken API that agents depend on leaves agents unable to function. The intent — fast, reliable rollback — matters more than the exact time threshold. Organizations with canary + circuit breaker patterns achieve safe recovery.

**Surface-flag calibration:** If `has_http_rpc_surface` is `false`, there is no deployed surface to roll back — record as INFO with the rationale `"No deployed HTTP/RPC surface — deployment rollback is a consumer concern. Library rollback is handled via package version pinning by consumers."` If the repo was classified as `dev-library-application` via Step 1.5, record as INFO.

**Look for:**
- Blue/green deployment config
- CodeDeploy rollback triggers
- Helm rollback
- Feature flags
- Canary deployment with automatic rollback
- Traffic shifting at API Gateway or ALB

---

#### ENG-Q4: API Test Coverage — RISK-QUALITY

**Question:** Are there automated tests for the APIs agents will consume — validating input handling, output format, error responses, and edge cases — running in CI?

**Why it matters:** APIs are the contract between agent and target system. If behavior changes without test coverage catching it, agents reason incorrectly.

**Look for:**
- API test suites (Postman/Newman collections, pytest API tests, REST Assured)
- Contract tests
- Integration test directories
- API test steps in CI pipeline configuration

---

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK-QUALITY

**Question:** Is data encrypted at rest (KMS) for sensitive information that agents will access?

**Why it matters:** Agents access data stores containing PII and business-sensitive information. Unencrypted data at rest means a breach exposes everything the agent can access.

**Look for:**
- `kms_key_id` on S3/RDS/DynamoDB/EBS
- Customer-managed KMS keys
- Encryption config in IaC

---
