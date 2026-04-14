# Agentic Readiness Assessment Guide

**A framework for assessing whether enterprise systems are safe, operable, and integrable as agent tools and resources.**

AWS Agentic Practice | Version 2.1 | April 2026

---

## What Is Agentic Readiness?

Agentic Readiness is the state where an enterprise can safely support autonomous AI systems that make decisions independently, call APIs, orchestrate multi-step workflows, and operate within appropriate boundaries. This readiness spans both technical and organizational dimensions: the underlying technical and operational foundation must be prepared for autonomous operations, and business processes must be well-understood and decomposable so teams know where agents should operate.

This framework evaluates the **environment** — infrastructure, applications, data, security controls, and operational practices — not the agent itself. It answers the question: are the systems agents will call ready to be called safely?

---

## How to Use This Guide

Run this assessment once per application or data domain. Each question carries a severity designation:

| Severity | Meaning | Implication |
|----------|---------|-------------|
| **BLOCKER** | Must resolve before any agent deployment. | Creates compliance exposure, data integrity risk, or failure-at-scale risk. |
| **RISK** | Can proceed with compensating controls, scoped pilots, or human-in-the-loop gates. | Track and remediate on a defined timeline. |
| **INFO** | No immediate gating impact. Shapes architecture decisions. | Feeds agent design and orchestration decisions. Not a deployment gate. |

**Readiness threshold:** No BLOCKERs and fewer than 3 unmitigated RISKs before broad agent deployment. The threshold applies per use-case scope — a read-only agent has a different risk profile than a write-enabled one.

### Use-Case Scoping

The BLOCKER threshold is use-case conditional. A read-only agent (Q&A, summarization, retrieval) has a meaningfully different risk profile than a write-enabled agent (order creation, payment, data modification). For conditional BLOCKERs (marked with ⚡), evaluate against the actual agent scope, not a worst-case assumption. Document the scope explicitly as part of the assessment output.

### Scope Boundary

This assessment covers **target systems only** — the applications and data that an agent will call or consume. It does NOT cover:

- **Agent architecture** — Agent orchestration design, tool-calling policies, prompt engineering, model selection, RAG pipeline design, vector store provisioning, agent evaluation frameworks, agent-level kill switches, prompt injection defenses, multi-agent coordination, MCP server implementation.
- **General cloud modernization** — Managed compute vs EC2, monolith decomposition, async messaging patterns, deployment strategies, and DevOps maturity. These belong in the Modernization Readiness Assessment.

### Who Should Run This

Run this assessment jointly between application owners, platform engineering, security, and whoever is designing the agent. Questions answered only by one team are answered incompletely.


---

## Data Sources

- Infrastructure as Code (Terraform, CloudFormation, CDK, ACK, KRO)
- Declarative Config (Helm Charts, Kustomize, Ansible)
- Dependency manifests (package.json, requirements.txt, pom.xml, go.mod, *.csproj)
- API specifications (OpenAPI/Swagger, AsyncAPI, GraphQL schemas, Smithy models)
- Code repositories (GitHub, GitLab, CodeCommit)
- AWS resource inventory (via AWS Config)
- CI/CD pipeline configurations (.github/*, buildspec.yml, Jenkinsfile)
- Container definitions (Dockerfile, docker-compose.yml)

---

## Repository Type Classification

Before running the assessment, the repository must be classified. This classification determines which questions apply (some are N/A for non-application repos). The Power orchestrator performs this classification and passes `repo_type` to the TD. Users can override via `repo_type` in the portfolio config.

**Classification Decision Tree:**

| Repo Type | Detection Rule | Example |
|-----------|---------------|---------|
| `application` | Source code files exist with a deployable entry point (main(), server.listen(), Dockerfile, IaC) | Java service, Python API, Node.js app |
| `infrastructure-only` | Only IaC provisioning files exist (Terraform, CDK, CloudFormation) with no source code and no deployment configs | Terraform modules, CDK stacks, CloudFormation templates |
| `deployment-config` | Only deployment configurations, CI/CD definitions, or operational manifests exist — no application source code. Includes: CI/CD pipelines (GitHub Actions, Jenkinsfile, buildspec.yml), Kubernetes manifests (Helm charts, Kustomize overlays, ArgoCD app definitions), GitOps configs, Ansible playbooks, service mesh configs, environment definitions. | Helm chart repos, GitOps config repos, CI/CD pipeline repos, Ansible playbook repos |
| `monorepo` | Multiple independent service directories with separate build configs | Monorepo with services/ dirs each with own package manifest |
| `library` | Package manifest exists but no deployable entry point (no Dockerfile, no IaC, no main()) | Internal SDK, shared utilities package |

The `repo_type` is passed as `additionalPlanContext` to the TD. Users can always override via `repo_type` in the portfolio config.

**N/A Questions by Repo Type (ARA):**

| Repo Type | Questions Scored as N/A |
|-----------|----------------------|
| `application` | None — all questions apply |
| `infrastructure-only` | API-Q1 through API-Q10, AUTH-Q4/Q5, STATE-Q1 through STATE-Q7, HITL-Q1 through HITL-Q3, DATA-Q1 through DATA-Q8, DISC-Q1 through DISC-Q4 |
| `deployment-config` | Most questions N/A except ENG-Q1 through ENG-Q6 and AUTH-Q1 through AUTH-Q3 |
| `library` | ENG-Q1 through ENG-Q6 are N/A (no deployment infrastructure) |
| `monorepo` | None — all questions apply (assessed per-service within the repo) |

**How the TD Uses repo_type:**

1. Read `repo_type` from `additionalPlanContext`. If not provided, default to `application`.
2. Before evaluating each section, check the N/A mapping above. If a question is N/A for the detected repo type, skip evaluation and record it as:
   - **Severity**: N/A
   - **Finding**: This is a `{repo_type}` repository. This question does not apply.
   - **Gap**: N/A
   - **Recommendation**: N/A
3. N/A questions are excluded from BLOCKER/RISK/INFO counts and do not affect the readiness profile.
4. If ALL questions in a section are N/A, skip the section entirely in the report.
5. All questions must still appear in the report — N/A questions are listed with the N/A format, not omitted.

---

## 01 — API Surface and Interface Design

### API-Q1: Documented API Interface — BLOCKER

**Question:** Does the application expose a documented REST, GraphQL, or AsyncAPI interface, or does integration require direct database access, file-based exchange, or UI automation?

**Why it matters:** Agent tools must bind to stable, predictable interfaces. Direct database or file-based integration creates brittle, non-auditable coupling. UI automation (RPA) is fragile and unscalable. An API is the minimum viable integration surface.

> Look for: REST endpoints in code (Express routes, Flask/FastAPI routes, Spring @RestController); GraphQL schema files; AsyncAPI specs; direct database connection strings in client-facing code; file-based data exchange patterns; Selenium/Puppeteer/RPA scripts.


### API-Q2: Machine-Readable API Specification — RISK

**Question:** Is there an OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification available and kept current with the implementation?

**Why it matters:** Agent frameworks use machine-readable specs to generate tool definitions automatically. Without one, every integration requires manual tool authoring that drifts from actual behavior. Classified as RISK (not BLOCKER) because GraphQL schemas, Smithy models, and well-documented SDKs serve the same purpose — the real blocker is no machine-readable interface at all (API-Q1).

> Check: Is the spec auto-generated from annotations (preferred) or manually maintained? When was it last updated relative to the last API change?

### API-Q3: Structured Error Responses — RISK

**Question:** Do API responses include structured error codes and machine-readable error bodies — not just HTTP status codes?

**Why it matters:** Agents need to distinguish retriable errors (timeout, rate limit) from terminal errors (invalid input, permission denied). A 500 with no body forces agents to guess.

> Minimum: error code, error message, and a retryable boolean or category.

### API-Q4: Idempotent Write Operations — BLOCKER ⚡

**Question:** Are write API endpoints idempotent?

**⚡ Conditional:** BLOCKER when agents have write access. For read-only agents, classify as INFO.

**Why it matters:** Agents retry on failure. LLM non-determinism can cause duplicate tool calls. A non-idempotent write endpoint will duplicate orders, payments, or records on retry. Data integrity risk at machine speed.

> Check: Does POST /orders with the same idempotency key create one record or two?

### API-Q5: API Versioning and Deprecation — RISK

**Question:** Are API contracts versioned, and is there a deprecation policy that includes downstream notification?

**Why it matters:** Agent tool schemas break silently when APIs change without notice. Every breaking change requires updating tool definitions and revalidating agent behavior.

> Look for: /v1/, /v2/ URL patterns; Accept-Version headers; versioning annotations; changelog files; deprecation notices in API docs.


### API-Q6: Structured Response Format — INFO

**Question:** What is the response format from service APIs? Structured JSON? XML? Binary?

**Why it matters:** LLMs consume text-based formats effectively. Complex XML or binary formats require extra parsing logic. Well-documented JSON APIs can be exposed as agent tools with minimal adaptation.

> Look for: Response serialization in code; content-type headers; protobuf/Thrift definitions; XML marshaling; JSON serialization libraries.


### API-Q7: Asynchronous Operation Support — RISK

**Question:** Does the application support async patterns for long-running tasks (job submission, polling endpoint, or webhook callback)?

**Why it matters:** Agents operating synchronously against long-running operations will hit timeout limits and create orphaned processes. Async patterns are required for any operation exceeding 30 seconds.

> Look for: Background job frameworks (Celery, Bull, SQS workers); async/polling patterns; job status APIs; Lambda async invocations; Step Functions for long processes; webhook callback endpoints.


### API-Q8: Event Emission for State Changes — INFO

**Question:** Can the system emit events or webhooks for meaningful state changes that agents may need to react to — such as record updates, status transitions, or completion of long-running operations?

**Why it matters:** Request/response agents are reactive. Event-driven patterns unlock proactive agents that respond to real-world changes without polling. INFO for now because most initial deployments are request-driven, but becomes RISK when the use case requires time-sensitive reaction.

> Look for: webhook endpoints, SNS/EventBridge/SQS integration, Kafka topics, CDC pipelines.

### API-Q9: Rate Limit Documentation and Headers — INFO

**Question:** Are API rate limits documented, and does the application return rate limit headers (X-RateLimit-Remaining, Retry-After)?

**Why it matters:** Agents call endpoints at machine speed without rate limit awareness. Undocumented limits cause unpredictable failures. Rate limit headers allow agents to self-throttle.

> Look for: API Gateway throttle settings; WAF rate rules; rate limiting middleware; X-RateLimit-Remaining headers in response code; `aws_api_gateway_usage_plan` in IaC.


### API-Q10: API Latency Profile — INFO

**Question:** What is the P95 response time for the APIs agents will consume?

**Why it matters:** An agent calling 5 tools sequentially, each with a 5-second P95, creates a 25-second minimum response time. This shapes whether to use sync or async patterns.

> Benchmark: Sub-second P95 ideal. 1–5s acceptable with caching. Over 5s should use async (API-Q7).


---

## 02 — Authentication, Authorization, and Identity

### AUTH-Q1: Machine Identity Authentication — BLOCKER

**Question:** Does the application support service account or machine identity authentication (client credentials OAuth 2.0, API key with principal attribution, or mTLS), and can the authenticated principal be attributed in audit logs?

**Why it matters:** Agents cannot use human credentials. The application must distinguish which agent made a call — a generic service account with no attribution is insufficient for audit and forensics.

> Look for: OAuth2 client credentials flow; API key authentication with principal attribution; mTLS configuration; service account definitions; Cognito app clients; API Gateway authorizers. Check audit logs for agent identity fields.


### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK

**Question:** Does the authorization model support scoped permissions — an agent identity can be granted read-only access to specific resources without inheriting broader privileges?

**Why it matters:** Agents under overly broad permissions create blast radius risk. Least-privilege is critical, though enforcement can happen at the platform layer (API Gateway, IAM policies) if the app itself is coarse-grained.

> Look for: IAM policies with specific actions per resource vs wildcards (Action: "*", Resource: "*"); role-per-service vs shared roles; API Gateway resource policies; condition keys in IAM policies.


### AUTH-Q3: Action-Level Authorization — RISK

**Question:** Can the application enforce action-level authorization — allowing an agent to read records but not delete them, even within the same resource type?

**Why it matters:** Action-level authorization (ABAC or fine-grained RBAC) is required for agents executing multi-step workflows with mixed read/write operations.

> Look for: ABAC policies; fine-grained RBAC definitions; permission matrices in code; action-level checks in middleware (canRead, canWrite, canDelete); API Gateway method-level authorization.


### AUTH-Q4: Identity Propagation — RISK

**Question:** Does the system support token exchange mechanisms (JWT/OAuth, on-behalf-of flows) that carry the originating user context end-to-end through service calls?

**Why it matters:** Without technical identity propagation, the system either cannot personalize responses per user or silently exposes all user data to every agent call.

> Look for: JWT parsing middleware; OAuth2 on-behalf-of flows; token exchange patterns; Cognito/Okta integration; user context headers (X-User-Id, Authorization Bearer) passed through service calls.


### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User — RISK

**Question:** Can the system distinguish between an agent acting under its own service identity and an agent acting on behalf of a specific human user? Are these two modes logged and authorized separately?

**Why it matters:** These are fundamentally different access patterns. An agent acting as itself should have tightly scoped permissions. An agent acting on behalf of a user should be bounded by that user's permissions, not the agent's broader service account. Conflating the two is a common source of privilege escalation.

> Look for: Separate IAM roles or API keys for agent-as-self vs agent-on-behalf-of-user; different auth flows for service-to-service vs user-delegated calls; audit log fields distinguishing the two modes.


### AUTH-Q6: Credential Management — RISK

**Question:** Are credentials managed through a secrets management system (AWS Secrets Manager, HashiCorp Vault) with rotation, or are they embedded in code, environment variables, or configuration files?

**Why it matters:** Hardcoded credentials are a security vulnerability — a prompt injection attack or agent bug could leak them. Assess whether secret rotation breaks agent continuity.

> Look for: `aws_secretsmanager_*` in IaC; Vault client imports; hardcoded patterns (password=, secret=, api_key= in code); .env files committed to git; environment variables with credential values in docker-compose or task definitions.


### AUTH-Q7: Immutable Audit Logging — BLOCKER ⚡

**Question:** Does the application log the authenticated principal for every write operation, and is that log immutable and tamper-evident?

**⚡ Conditional:** BLOCKER for regulated data contexts (EU AI Act, HIPAA, SOX). RISK for non-regulated contexts.

**Why it matters:** Audit trails must identify whether an action was taken by a human or an agent, and which specific agent instance. Without immutable logs, you cannot prove compliance or conduct forensics.

> Look for: `aws_cloudtrail` in IaC; CloudTrail log file validation enabled; S3 bucket with object lock for logs; CloudWatch log retention policies; immutable log storage configuration.


### AUTH-Q8: Agent Identity Suspension — RISK

**Question:** Can individual agent identities be suspended or revoked immediately if anomalous behavior is detected, without taking down the broader platform?

**Why it matters:** The ability to isolate a misbehaving agent without disrupting other agents or users is a fundamental operational requirement.

> Look for: API key revocation endpoints; IAM role deactivation procedures; service account disable mechanisms; Cognito user pool user disable; API Gateway API key deletion.


---

## 03 — State Management and Transactional Integrity

### STATE-Q1: Compensation and Rollback — BLOCKER ⚡

**Question:** Does the application support compensation or rollback for multi-step operations that fail mid-sequence?

**⚡ Conditional:** BLOCKER when agents execute write-enabled multi-step workflows. For read-only agents, classify as RISK.

**Why it matters:** Agents executing a 5-step workflow may succeed on steps 1–4 and fail on step 5. Without rollback or compensation logic, the application is left in a partial state.

> Patterns: saga pattern, two-phase commit, explicit undo endpoints, compensating transactions.

> Patterns to look for: saga pattern, two-phase commit, explicit undo endpoints, compensating transactions, Step Functions with error handling and rollback states.


### STATE-Q2: Queryable Current State — RISK

**Question:** Does the application expose its current state in a queryable form that an agent can inspect before taking action?

**Why it matters:** Agents need to read current state before deciding next steps. Write-only or event-only interfaces force agents to maintain external state, introducing synchronization risk.

> Look for: GET endpoints for resource state; status query APIs; read-before-write patterns in code; state machine status fields in database schemas.


### STATE-Q3: Concurrency Controls — RISK

**Question:** Does the application support optimistic locking or concurrency controls to prevent race conditions when multiple agent instances operate simultaneously?

**Why it matters:** Multiple agent instances may attempt concurrent writes. Without concurrency controls (optimistic locking, ETags, version fields), data integrity is at risk.

> Look for: Optimistic locking (version fields, ETags, If-Match headers); pessimistic locking (SELECT FOR UPDATE); DynamoDB conditional writes; conflict resolution logic.


### STATE-Q4: Circuit Breakers and Resilience — RISK

**Question:** Does the target system implement circuit breakers, retry logic, and timeout configurations for its own external dependency calls?

**Why it matters:** When an agent calls the target system, that request may trigger cascading calls to the system's own dependencies. Circuit breakers prevent the target system from becoming a bottleneck that cascades failures back to the agent.

> Look for: Resilience4j, Polly, retry decorators, exponential backoff, @CircuitBreaker annotations.

### STATE-Q5: Rate Limiting and Throttling — RISK

**Question:** Are rate limits enforced at the API layer to prevent runaway agent loops from overwhelming the application?

**Why it matters:** A runaway agent loop can DDoS your own services at machine speed. Rate limiting prevents agent bugs from taking down production.

> Look for: API Gateway throttling config; WAF rate rules; application-level rate limiting middleware (express-rate-limit, django-ratelimit); `aws_api_gateway_usage_plan` in IaC.


### STATE-Q6: Blast Radius and Transaction Limits — RISK

**Question:** Can the system enforce configurable limits on agent-initiated actions — such as maximum records modified per run, maximum spend per hour, or maximum delete operations per session — independently of general rate limits?

**Why it matters:** Rate limits (STATE-Q5) protect the system from traffic overload. Transaction limits protect the business from the consequences of an agent executing correct-but-catastrophic logic — deleting 10,000 records instead of 100, or issuing $50,000 in refunds in a loop. These limits define the maximum blast radius of an agent error.

> Examples: max_refunds_per_hour=50, max_records_per_bulk_operation=500, max_spend_per_session=$1000. Configurable per agent identity, not just per API endpoint.

### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK

**Question:** Is the backend infrastructure sized and tested for the unpredictable, exploratory traffic patterns that agents generate?

**Why it matters:** APIs designed for human-paced interaction are load-tested for known traffic profiles. Agents don't respect those assumptions — they explore, retry, and fan out. Agent-induced load can starve unrelated systems sharing the backend.

> Look for: Load test results or configurations; auto-scaling policies; capacity planning documentation; circuit breakers isolating agent traffic from other consumers.


---

## 04 — Human-in-the-Loop and Approval Workflows

### HITL-Q1: Draft/Pending State — RISK

**Question:** Does the application have the concept of a pending or draft state that an agent can write to before a human approves and commits?

**Why it matters:** Agents should not commit irreversible actions autonomously for high-stakes operations. Draft states let agents propose and humans confirm.

> Look for: Draft/pending status fields in database schemas; approval workflow endpoints; two-step commit patterns (create-then-confirm); status-based state machines.


### HITL-Q2: Configurable Approval Gates — RISK

**Question:** Can specific operations be configured to require a human approval step before the application executes them — configurable by operation type?

**Why it matters:** High-risk actions benefit from human-in-the-loop approval at the application layer as defense in depth, even when orchestration-layer gates exist.

> Look for: Approval API endpoints; status-based workflows requiring explicit confirmation; configurable operation-level flags; Step Functions with human approval tasks (waitForTaskToken).


### HITL-Q3: Sandbox/Staging Environment — RISK

**Question:** Is there a sandbox or staging environment with production-equivalent data shape that agents can use for testing without risk to live systems?

**Why it matters:** Agents must be testable against realistic conditions before production promotion. Without a staging environment, the first time you discover an agent bug is in production.

> Look for: Separate environment configurations (staging, sandbox); docker-compose for local testing; seed data scripts; synthetic data generators; environment-specific IaC.


---

## 05 — Data Accessibility and Quality

### DATA-Q1: Sensitive Data Classification — BLOCKER

**Question:** Is sensitive data (PII, PHI, financial records, credentials) classified and tagged at the field level, and are there controls preventing an agent from retrieving it without explicit authorization?

**Why it matters:** Unclassified sensitive data in a retrieval pipeline is a regulatory and reputational risk. Classification must happen before agents get read access.

> Look for: Data classification tags in IaC (aws_s3_bucket tags, DynamoDB table tags); field-level encryption; column-level access controls; PII detection tools (Macie); data classification policies in documentation.


### DATA-Q2: Data Residency and Sovereignty — BLOCKER ⚡

**Question:** Is the data subject to residency or sovereignty requirements that would restrict an agent from transmitting it to an LLM provider in a different region or jurisdiction?

**⚡ Conditional:** BLOCKER for regulated data (GDPR, LGPD, HIPAA, sector-specific). RISK if no regulated data is in scope.

**Why it matters:** An agent sending regulated data to an LLM endpoint in another region may create a legal violation. The data residency constraints are properties of the data the system holds.

> Look for: Data residency requirements in documentation; GDPR/LGPD compliance references; region-specific data storage configurations; cross-region replication settings; data sovereignty policies.


### DATA-Q3: Selective Query Support — RISK

**Question:** Can data be queried with filters, pagination, and sorting that limit result set size to what an agent actually needs?

**Why it matters:** Agents retrieving unbounded result sets exhaust LLM context windows and increase cost.

> Look for: Pagination parameters in API endpoints (limit, offset, cursor); filter query parameters; sorting options; GraphQL field selection; result size limits in API documentation.


### DATA-Q4: System of Record Designations — RISK

**Question:** Are there authoritative system-of-record designations for key entities, and is there a master data management process that resolves conflicts across systems?

**Why it matters:** Agents reasoning across multiple systems will encounter conflicting records. Without a golden record, decisions will be inconsistent.

> Look for: Master data management references; system-of-record designations in documentation; data ownership definitions; conflict resolution logic; golden record patterns.


### DATA-Q5: Reliable Timestamps — RISK

**Question:** Does the data include reliable, timezone-normalized timestamps for creation, last update, and source event time?

**Why it matters:** Agents performing time-sensitive reasoning depend on accurate temporal data. Missing or unreliable timestamps cause silent errors.

> Look for: created_at, updated_at, event_time fields in database schemas; timezone handling (UTC storage); timestamp format consistency; NTP synchronization configuration.


### DATA-Q6: Data Freshness Signaling — RISK

**Question:** Can the system indicate whether data returned to an agent is current, stale, cached, or eventually consistent? Does it expose cache age, last-refreshed timestamps, or consistency guarantees at the response level?

**Why it matters:** Agents make consequential decisions fast based on data retrieved seconds ago. If the system cannot signal that data is cached or eventually consistent, the agent has no way to know whether it is reasoning on the current state. Distinct from DATA-Q6 (data timestamps) — this covers the freshness of the retrieval itself.

> Examples: Cache-Control headers, X-Data-Age, last_refreshed field, consistency_level field (strong / eventual / cached).

### DATA-Q7: PII Redaction in Logs — RISK

**Question:** Is PII redacted from logs, error messages, and observability data?

**Why it matters:** Agents process customer PII. If PII leaks into logs or LLM prompt/response pairs, it becomes a compliance violation.

> Look for: Log scrubbing middleware; PII masking libraries; CloudWatch log filters; Amazon Macie integration; regex patterns for PII in logging utilities.


### DATA-Q8: Data Quality Awareness — INFO

**Question:** Is there a known data quality score or completeness metric for this dataset?

**Why it matters:** Agents acting on incomplete or stale data propagate errors faster than human workflows. Planning input, not a deployment blocker.

> Look for: Data quality dashboards; data profiling reports; null rate monitoring; duplicate detection logic; data freshness SLAs; data quality metrics in observability.


---

## 06 — Discoverability and Semantic Readiness

### DISC-Q1: Schema Documentation and Versioning — RISK

**Question:** Are data schemas documented, versioned, and accessible?

**Why it matters:** Agents need to understand data structures. Schema changes without versioning break agent queries silently.

> Look for: JSON Schema files, Avro/Protobuf schemas, database migration files, schema registry, OpenAPI schema definitions.

### DISC-Q2: Semantically Meaningful Field Names — INFO

**Question:** Are field names and identifiers human-readable and semantically meaningful, or are they legacy codes requiring a data dictionary?

**Why it matters:** Agents using LLM-based reasoning need interpretable field names. `CUST_TYP_CD` requires a lookup. `CustomerTypeCode` does not.

> Look for: Field naming conventions in database schemas and API responses; legacy abbreviations (CUST_TYP_CD vs CustomerTypeCode); data dictionary files; naming convention documentation.


### DISC-Q3: Data Catalog / Metadata Layer — INFO

**Question:** Is there a data catalog or metadata layer describing what data the target system holds and what it means semantically?

**Why it matters:** Accelerates tool definition when building agent tools against this system.

> Tools: AWS Glue Data Catalog, Collibra, Alation, DataHub. Look for: metadata files, data dictionaries, schema documentation, API catalogs.


### DISC-Q4: Data Lineage — INFO

**Question:** Is there a lineage record showing where each data element originated and how it was transformed?

**Why it matters:** When an agent produces incorrect output due to bad data, lineage is how you trace it.

> Look for: Data lineage tools (AWS Glue DataBrew, Apache Atlas); ETL pipeline documentation; data flow diagrams; transformation logs; source-to-target mappings.


---

## 07 — Observability of Target Systems

### OBS-Q1: Distributed Tracing and Structured Logging — RISK

**Question:** Does the application support distributed tracing (X-Ray, OpenTelemetry) with trace ID propagation, and are logs structured (JSON) with correlation IDs linking all entries for a single request?

**Why it matters:** These two controls serve the same diagnostic purpose — reconstructing what happened inside the target system when an agent-initiated request fails. Both must be present to make agent-initiated failures debuggable.

> Look for: OpenTelemetry SDK, X-Ray instrumentation, traceparent header propagation, JSON logs, request_id or correlation_id field.

### OBS-Q2: Alerting on Error Rates and Latency — RISK

**Question:** Are there alerting thresholds configured for error rates and latency on the APIs agents will consume?

**Why it matters:** Target system degradation is felt immediately by agents. Alerting lets you detect problems before agents start cascading failures.

> Look for: CloudWatch alarms on error rates and latency; anomaly detection configuration; PagerDuty/OpsGenie integration; composite alarms; SLO-based alerting.


### OBS-Q3: Business Outcome Metrics — INFO

**Question:** Are custom metrics published for business outcomes, not just infrastructure metrics?

**Why it matters:** When agents consume the system, business metrics become the primary signal for whether agent interactions produce good outcomes.

> Look for: cloudwatch.put_metric_data for business events; custom dashboards tracking resolution rates, conversion, satisfaction; business KPI alarms.


---

## 08 — Engineering and Deployment Maturity

### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK

**Question:** Is the infrastructure exposing the target system to agents — API gateways, IAM roles, secrets, network configurations — defined as code, subject to peer review before changes, and monitored for drift?

**Why it matters:** The integration surface is a high-value attack surface. All three controls — IaC definition, change review, and drift detection — must be present together for this surface to be trustworthy.

> Sub-checks: (1) Integration surface defined as IaC? (2) Changes subject to automated plan review + peer review? (3) Drift detection active?

### ENG-Q2: CI/CD with API Contract Testing — RISK

**Question:** Does the target system have a CI/CD pipeline that includes automated testing of agent-facing APIs and the ability to detect API-breaking changes before production?

**Why it matters:** The agentic concern is not "does CI/CD exist" but "can API contract changes be caught before agents are affected."

> Look for: API contract tests in CI pipeline; consumer-driven contract testing (Pact); OpenAPI spec validation in build; schema comparison tools; breaking change detection.


### ENG-Q3: Rollback Capability — RISK

**Question:** Can the target system's deployment be rolled back to the previous known-good state if a change breaks agent-facing APIs? (Target: within 15–30 minutes.)

**Why it matters:** A broken API that agents depend on leaves agents unable to function. The intent — fast, reliable rollback — matters more than the exact time threshold. Organizations with canary + circuit breaker patterns achieve safe recovery.

> Look for: Blue/green deployment config; CodeDeploy rollback triggers; Helm rollback; feature flags; canary deployment with automatic rollback; traffic shifting at API Gateway or ALB.


### ENG-Q4: API Test Coverage — RISK

**Question:** Are there automated tests for the APIs agents will consume — validating input handling, output format, error responses, and edge cases — running in CI?

**Why it matters:** APIs are the contract between agent and target system. If behavior changes without test coverage catching it, agents reason incorrectly.

> Look for: API test suites (Postman/Newman collections, pytest API tests, REST Assured); contract tests; integration test directories; API test steps in CI pipeline configuration.


### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK

**Question:** Is data encrypted at rest (KMS) for sensitive information that agents will access?

**Why it matters:** Agents access data stores containing PII and business-sensitive information. Unencrypted data at rest means a breach exposes everything the agent can access.

> Look for: kms_key_id on S3/RDS/DynamoDB/EBS, customer-managed KMS keys, encryption config.

### ENG-Q6: Cross-Origin and Network Policies — BLOCKER

**Question:** Are CORS policies and network security configurations (security groups, firewall rules, API gateway settings) documented and discoverable, regardless of whether they are defined in application code, infrastructure-as-code repos, or centralized configuration systems?

**Why it matters:** Agents running on cloud platforms must traverse network boundaries. Misconfigured CORS or firewall rules block integration entirely. These configurations may exist in application repos, infrastructure repos (Terraform/CloudFormation), API gateway configs, or service mesh policies.

> Look for: CORS configuration in API Gateway or application middleware; security group rules in IaC; firewall rules; network policies in Kubernetes; API gateway access policies; WAF rules.


---

## 09 — Scoring and Prioritization

### Readiness Profiles

| Readiness Profile | Blockers | Unmitigated Risks | Recommendation | Deployment Gate |
|---|---|---|---|---|
| **Agent-Ready** | 0 | 0–2 | Broad deployment | Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first. |
| **Pilot-Ready** | 0 | 3–5 | Narrow pilot only | Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope. |
| **Remediation Required** | 1–2 | Any | Remediate first | Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. |
| **Not Agent-Integrable** | 3+ | Any | Deferred or descoped | Exclude from agent toolset or plan major remediation before re-evaluation. |

### Remediation Guidance

There is no universal remediation order — it depends on the use case, the blockers found, and the organization's constraints. However, the following principles apply:

- **Resolve BLOCKERs first.** No agent deployment (including pilots) should proceed with open BLOCKERs. Start with whichever blocker is fastest to resolve to unblock a scoped pilot.
- **Identity before data access.** If both identity (AUTH-Q1) and data classification (DATA-Q1) are blockers, fix identity first — you cannot enforce data access controls without knowing who is calling.
- **Read-only before write-enabled.** If write-operation blockers (API-Q4, STATE-Q1) are present, consider scoping the initial agent to read-only operations while remediating write safety. This unblocks value faster.
- **RISKs are prioritized by use case.** A RISK that is irrelevant to the planned agent scope can be deferred. A RISK that directly affects the planned scope should be treated with urgency.
- **Compensating controls buy time, not exemptions.** A RISK mitigated by a compensating control (e.g., human-in-the-loop gate) is acceptable for a pilot but must be remediated before expanding scope.

### Portfolio-Level Guidance

Run this assessment across your top 20 application and data assets first. You do not need 100% of your portfolio agent-ready to launch. You need the right 5–10 systems ready for the first 2–3 use cases. Sequence agent deployment to start with the cleanest integration surface, then expand as you remediate harder systems in parallel.

### Agentic Programs and Engagement Recommendations

These program recommendations apply at the portfolio level when aggregating ARA results across multiple repos:

| Program | Trigger Condition |
|---------|-------------------|
| Experience-Based Acceleration (EBA) — Agentic AI | Portfolio has 3+ repos classified as Pilot-Ready or Remediation Required |
| Agentic Readiness Workshop | Portfolio has repos with 2+ BLOCKERs and teams need guidance on remediation sequencing |
| AgentCore Enablement | Portfolio has repos classified as Agent-Ready and teams are ready to build agent integrations |

These are distinct from the modernization programs (MAP, OLA, MMP, etc.) which are triggered by the Modernization Assessment. Agentic programs focus on enabling safe agent deployment, not cloud architecture modernization.

---

## What This Assessment Does Not Cover

- **Agent architecture and design** — Agent orchestration, tool-calling policies, prompt engineering, model selection, RAG pipeline design, vector store provisioning, agent evaluation frameworks, agent-level kill switches, LLM cost attribution, agent replay infrastructure, prompt injection defenses, multi-agent coordination, MCP server implementation.
- **General cloud modernization** — Managed compute vs EC2, monolith decomposition, async messaging patterns, database migration, deployment strategies, and DevOps maturity. These belong in the Modernization Readiness Assessment.
- **COTS / third-party platforms** — This assessment targets systems you own and can change. Commercial off-the-shelf platforms (Salesforce, ServiceNow, SAP, Workday) have fixed interfaces you cannot modify — a failed assessment means scoping the agent differently or using a middleware adapter, not remediating the platform. That said, this framework can be used as a vendor evaluation checklist when selecting new tools or platforms — systems that score well on these criteria will be easier to integrate with agents.
- **Organizational readiness** — Change management, team structure, skill gaps, training programs, and executive sponsorship.

---

## Summary of Questions by Section and Severity

| Section | BLOCKER | RISK | INFO | Total |
|---------|---------|------|------|-------|
| 01 — API Surface and Interface Design | 2 | 4 | 4 | 10 |
| 02 — Authentication, Authorization, and Identity | 2 | 6 | 0 | 8 |
| 03 — State Management and Transactional Integrity | 1 | 6 | 0 | 7 |
| 04 — Human-in-the-Loop and Approval Workflows | 0 | 3 | 0 | 3 |
| 05 — Data Accessibility and Quality | 2 | 5 | 1 | 8 |
| 06 — Discoverability and Semantic Readiness | 0 | 1 | 3 | 4 |
| 07 — Observability of Target Systems | 0 | 2 | 1 | 3 |
| 08 — Engineering and Deployment Maturity | 1 | 5 | 0 | 6 |
| **Total** | **8** | **32** | **9** | **49** |

Note: Conditional BLOCKERs (⚡) are counted as BLOCKERs in the table. When evaluating for a read-only agent use case, API-Q4 and STATE-Q1 drop to INFO/RISK, reducing effective BLOCKERs to 6.

