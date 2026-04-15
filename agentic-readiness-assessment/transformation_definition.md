## Name

Agentic Readiness Assessment

## Objective

Evaluate whether a repository's systems — infrastructure, applications, data, security controls, and operational practices — are safe, operable, and integrable for autonomous AI agent integration. This assessment targets the environment that agents will call or consume, not the agent itself. It answers the question: are the systems agents will interact with ready to be called safely?

## Summary

This transformation performs a dedicated Agentic Readiness Assessment on a codebase. It scans all files in the repository to discover infrastructure-as-code, application source code, CI/CD definitions, API specifications, dependency manifests, configuration files, and container definitions. It then evaluates what it finds against 49 questions across 8 sections:

- **API** — API Surface and Interface Design (10 questions)
- **AUTH** — Authentication, Authorization, and Identity (8 questions)
- **STATE** — State Management and Transactional Integrity (7 questions)
- **HITL** — Human-in-the-Loop and Approval Workflows (3 questions)
- **DATA** — Data Accessibility and Quality (8 questions)
- **DISC** — Discoverability and Semantic Readiness (4 questions)
- **OBS** — Observability of Target Systems (3 questions)
- **ENG** — Engineering and Deployment Maturity (6 questions)

Each question is scored using a severity model:

| Severity | Meaning | Implication |
|----------|---------|-------------|
| **BLOCKER** | Must resolve before any agent deployment. | Creates compliance exposure, data integrity risk, or failure-at-scale risk. |
| **RISK** | Can proceed with compensating controls, scoped pilots, or human-in-the-loop gates. | Track and remediate on a defined timeline. |
| **INFO** | No immediate gating impact. Shapes architecture decisions. | Feeds agent design and orchestration decisions. Not a deployment gate. |

Four questions are **conditional BLOCKERs** (⚡) — their severity depends on the `agent_scope` context (write-enabled vs read-only): API-Q4, STATE-Q1, AUTH-Q7, and DATA-Q2.

Four additional questions are **scope-calibrated RISKs** (⚡) — they evaluate as RISK when `agent_scope` is `"write-enabled"` but downgrade to INFO when `agent_scope` is `"read-only"` because their concerns are specific to write operations: HITL-Q1, HITL-Q2, STATE-Q3, and STATE-Q6.

The output is a structured Markdown report saved as `{repo-name}-ara-report.md` containing:
- Metadata header (repo name, date, repo_type, agent_scope)
- Readiness profile (Agent-Ready, Pilot-Ready, Remediation Required, or Not Agent-Integrable)
- BLOCKER/RISK/INFO summary counts (excluding N/A questions)
- BLOCKERs section with remediation guidance
- RISKs section with compensating control options
- INFOs section
- Detailed findings for all 49 questions (including N/A questions in N/A format)
- Evidence index with file references

The readiness profile is determined by blocker and risk counts:

| Readiness Profile | Blockers | Risks | Recommendation |
|-------------------|----------|-------|----------------|
| **Agent-Ready** | 0 | 0–2 | Broad deployment |
| **Pilot-Ready** | 0 | 3–5 | Narrow pilot only |
| **Remediation Required** | 1–2 | Any | Remediate first |
| **Not Agent-Integrable** | 3+ | Any | Deferred or descoped |

This assessment does NOT cover agent architecture (orchestration design, prompt engineering, model selection, RAG pipelines, MCP servers) or general cloud modernization (managed compute, monolith decomposition, deployment strategies, DevOps maturity). Those concerns belong in the Modernization Readiness Assessment.

## Entry Criteria

- The repository is accessible and readable at the specified path
- The repository contains files relevant to assessment (source code, IaC, API specs, CI/CD configs, dependency manifests, container definitions, or configuration files)
- Write permissions exist to create the output report file
- The assessment operates in **read-only mode** — it will not modify any source code or configuration in the repository

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning the discovery scan, read the assessment context from `additionalPlanContext` to determine the repo classification, agent scope, and framing context that will shape the entire assessment.

#### 0.1 Read Assessment Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `repo_type` | enum | No | `"application"` | Repository classification. One of: `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`. Determines which questions are scored as N/A. |
| `agent_scope` | enum | No | `"read-only"` | The intended agent access level. One of: `read-only`, `write-enabled`. Determines severity of conditional BLOCKER (⚡) questions. |
| `context` | string | No | — | Free-text description of the repository (e.g., "Legacy PHP e-commerce app running on EC2 with MySQL"). Used to frame findings and recommendations throughout the report. |
| `priority` | enum | No | — | Repository priority within the portfolio. One of: `P0`, `P1`, `P2`. Recorded in report metadata. |
| `tags` | string[] | No | — | User-defined tags for categorization (e.g., `["monolith", "php", "payment-critical"]`). Recorded in report metadata. |

**Example `additionalPlanContext`:**

```yaml
additionalPlanContext: |
  repo_type: "application"
  agent_scope: "write-enabled"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  priority: "P0"
  tags: ["monolith", "php", "payment-critical"]
```

#### 0.2 Apply Defaults

If a field is absent from `additionalPlanContext`, apply these defaults:

- **`repo_type`** → `"application"` — This is the most comprehensive assessment (no questions skipped). Defaulting to `application` ensures nothing is missed when classification is unknown.
- **`agent_scope`** → `"read-only"` — This is the safer default. Conditional BLOCKER questions (⚡) are evaluated as INFO or RISK rather than BLOCKER, avoiding false escalation when the agent use case has not been scoped.
- **`context`** → No default. If absent, findings and recommendations are written without additional framing.
- **`priority`** → No default. If absent, omitted from report metadata.
- **`tags`** → No default. If absent, omitted from report metadata.

If `repo_type` is present but not one of the 5 recognized values (`application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`), default to `"application"` and include a warning in the report metadata: **"Unrecognized repo_type '{value}', defaulting to application."**

#### 0.3 Fields NOT Read by This TD

The ARA TD does **not** read, validate, or apply the following fields from `additionalPlanContext`. If present, they are ignored:

- **`goal`** — There is no goal system. Assessment routing is handled by `assessment_type` in the portfolio config, not by the TD. The ARA TD evaluates all 49 questions with equal weighting regardless of any goal value.
- **`goal_context`** — Replaced by the `context` field. The ARA TD uses `context` for free-text framing only.
- **`preferences`** — The `preferences` field (prefer/avoid arrays) is a MOD-only concept used for technology recommendation steering. The ARA TD evaluates agent safety and operability — it does not make technology recommendations that would be influenced by preferences.

#### 0.4 How Context Fields Are Used

Record the resolved values from Steps 0.1–0.2 in the assessment context. They will be used in subsequent steps as follows:

- **`repo_type`** → Used in the N/A Mapping (Step 1) to determine which questions are scored as N/A for the detected repo type. Included in the report metadata header.
- **`agent_scope`** → Used in Steps 2–9 (Evaluation) to determine the severity of conditional BLOCKER (⚡) questions: API-Q4, STATE-Q1, AUTH-Q7, and DATA-Q2. When `agent_scope` is `"write-enabled"`, these are evaluated as BLOCKERs. When `"read-only"`, they are evaluated as INFO or RISK. Also used to calibrate scope-sensitive RISK questions: HITL-Q1, HITL-Q2, STATE-Q3, and STATE-Q6 — these evaluate as RISK when `"write-enabled"` and downgrade to INFO when `"read-only"`. Included in the report metadata header.
- **`context`** → Used throughout the report to frame findings and recommendations with repository-specific context.
- **`priority`** → Recorded in the report metadata header.
- **`tags`** → Recorded in the report metadata header.

### Step 1: Discovery — Static Scan

Scan the target repository to build a complete inventory of what exists before evaluating any questions. This discovery step feeds every subsequent evaluation step — questions reference specific file types and patterns identified here.

#### 1.1 Scan the Repository

Get the full directory tree and identify all file types present. For each category below, locate and read all relevant files:

**Infrastructure as Code (IaC):**
- Terraform files (`.tf`, `.tfvars`)
- CloudFormation templates (`template.yaml`, `template.json`, `*.cfn.yaml`, `*.cfn.json`)
- CDK stacks (CDK app entry points, `cdk.json`, construct files)
- Helm charts (`Chart.yaml`, `values.yaml`, templates directory)
- Kustomize (`kustomization.yaml`, overlays, bases)
- ACK and KRO resource definitions
- Ansible playbooks (`.yml`, `.yaml` in playbook directories)

**Source Code:**
- Application source files (`.py`, `.java`, `.js`, `.ts`, `.go`, `.cs`, `.rb`, `.php`, `.rs`, `.kt`, `.scala`)
- Entry points (`main()`, `server.listen()`, `if __name__ == "__main__"`, `@SpringBootApplication`, `func main()`)
- Package manifests (`package.json`, `requirements.txt`, `pom.xml`, `build.gradle`, `go.mod`, `*.csproj`, `Cargo.toml`, `Gemfile`)

**API Specifications:**
- OpenAPI / Swagger files (`openapi.yaml`, `openapi.json`, `swagger.yaml`, `swagger.json`)
- AsyncAPI specifications
- GraphQL schema files (`.graphql`, `.gql`)
- Smithy models (`.smithy`)

**CI/CD Configurations:**
- GitHub Actions (`.github/workflows/*.yml`)
- GitLab CI (`.gitlab-ci.yml`)
- Jenkins (`Jenkinsfile`)
- AWS CodeBuild (`buildspec.yml`)
- AWS CodePipeline definitions in IaC
- Other pipeline definitions

**Container Definitions:**
- Dockerfiles (`Dockerfile`, `Dockerfile.*`)
- Docker Compose (`docker-compose.yml`, `docker-compose.*.yml`)
- Container image references in IaC or Kubernetes manifests

**Dependency Manifests:**
- Node.js (`package.json`, `package-lock.json`, `yarn.lock`)
- Python (`requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py`, `setup.cfg`)
- Java (`pom.xml`, `build.gradle`, `build.gradle.kts`)
- Go (`go.mod`, `go.sum`)
- .NET (`*.csproj`, `*.sln`, `packages.config`)
- Rust (`Cargo.toml`, `Cargo.lock`)
- Ruby (`Gemfile`, `Gemfile.lock`)

**Configuration Files:**
- Application config (`*.yaml`, `*.yml`, `*.json`, `*.toml`, `*.properties`, `*.ini`)
- Environment files (`.env`, `.env.*`)
- Kubernetes manifests (`*.yaml` in k8s/, manifests/, or deploy/ directories)
- Service mesh configs (Istio, App Mesh)

#### 1.2 Directories to Ignore

Skip the following directories during scanning — they contain installed dependencies, build artifacts, or version control internals that are not relevant to the assessment:

- `node_modules/` — Installed Node.js dependencies
- `target/` — Java/Maven build output
- `build/` — General build output directories
- `.git/` — Git version control internals
- `dist/` — Distribution / compiled output
- `vendor/` — Vendored dependencies (Go, PHP, Ruby)
- `.terraform/` — Terraform provider cache
- `__pycache__/` — Python bytecode cache
- `.venv/`, `venv/`, `env/` — Python virtual environments
- `bin/` — Compiled binaries (when clearly build output)

#### 1.3 Build the File Inventory

After scanning, compile a structured inventory of what was found. This inventory is referenced throughout Steps 2–9 when evaluating individual questions. Record:

- **IaC files found** — List of Terraform, CloudFormation, CDK, Helm, Kustomize, and other IaC files with their paths. Used by: AUTH-Q1 (IAM/auth config), AUTH-Q6 (secrets in IaC), AUTH-Q7 (CloudTrail config), ENG-Q1 (IaC governance), ENG-Q5 (encryption at rest), ENG-Q6 (network policies), STATE-Q5 (rate limiting in API Gateway), and others.
- **Source code files found** — List of application source files by language. Used by: API-Q1 (API endpoints in code), API-Q3 (error handling), API-Q4 (idempotency patterns), AUTH-Q2 (permission checks), STATE-Q3 (concurrency controls), STATE-Q4 (resilience patterns), and others.
- **API spec files found** — List of OpenAPI, AsyncAPI, GraphQL, and Smithy files. Used by: API-Q1 (documented interface), API-Q2 (machine-readable spec), DISC-Q1 (schema documentation).
- **CI/CD config files found** — List of pipeline definitions. Used by: ENG-Q2 (CI/CD with contract testing), ENG-Q3 (rollback capability), ENG-Q4 (API test coverage).
- **Container files found** — List of Dockerfiles and compose files. Used by: multiple infrastructure and deployment questions.
- **Dependency manifests found** — List of package manifests by ecosystem. Used by: identifying frameworks, libraries, and technology stack across multiple questions.
- **Configuration files found** — List of config files by type. Used by: AUTH-Q6 (hardcoded secrets), DATA-Q2 (data residency config), and others.
- **Notable absences** — Record what was NOT found. Absence is evidence: if no API spec files exist, that is a finding for API-Q2. If no IaC files exist, that is a finding for ENG-Q1. These absences are cited in evaluation steps.

#### 1.4 Read Discovered Files

Read all discovered files that are relevant to the assessment. Prioritize reading in this order:

1. **IaC files** — These reveal infrastructure architecture, security configuration, and deployment topology
2. **API specification files** — These reveal the integration surface agents will consume
3. **CI/CD configuration files** — These reveal deployment maturity and testing practices
4. **Dependency manifests** — These reveal technology stack, frameworks, and library choices
5. **Container definitions** — These reveal deployment packaging and runtime configuration
6. **Application source code** — These reveal implementation patterns, error handling, auth logic, and data access
7. **Configuration files** — These reveal runtime settings, environment configuration, and connection details

For large repositories, focus on files most relevant to the 49 evaluation questions. Not every source file needs to be read in full — prioritize entry points, API route definitions, authentication middleware, data access layers, and error handling patterns.

## N/A Mapping — Repository Type Question Applicability

Before evaluating any question, check the `repo_type` (resolved in Step 0) against the N/A mapping table below. Questions mapped as N/A for the detected repo type are **not evaluated** — they are recorded directly in the N/A display format and excluded from scoring.

### N/A Question Mappings by Repo Type

| Repo Type | Questions Scored as N/A |
|-----------|------------------------|
| `application` | None — all 49 questions apply |
| `infrastructure-only` | API-Q1 through API-Q10, AUTH-Q4, AUTH-Q5, STATE-Q1 through STATE-Q7, HITL-Q1 through HITL-Q3, DATA-Q1 through DATA-Q8, DISC-Q1 through DISC-Q4 |
| `deployment-config` | All questions N/A **except** ENG-Q1 through ENG-Q6 and AUTH-Q1 through AUTH-Q3 |
| `library` | ENG-Q1 through ENG-Q6 |
| `monorepo` | None — all 49 questions apply (assessed per-service within the repo) |

**Rationale by repo type:**

- **`application`** — Full-stack repositories with source code, APIs, data access, and deployment infrastructure. All 49 questions are relevant because agents will interact with the application's APIs, data, auth, and operational surface.
- **`infrastructure-only`** — Repositories containing only IaC provisioning (Terraform modules, CDK stacks, CloudFormation templates) with no application source code. API, most application-level auth (identity propagation, agent-as-self), state management, human-in-the-loop, data accessibility, and discoverability questions do not apply because there is no application runtime to evaluate. Auth questions AUTH-Q1 through AUTH-Q3 and AUTH-Q6 through AUTH-Q8 still apply (machine identity, scoped permissions, action-level auth, credential management, audit logging, agent suspension) because IaC defines IAM roles, policies, and security controls. OBS and ENG questions still apply because infrastructure repos define observability and deployment maturity.
- **`deployment-config`** — Repositories containing only CI/CD pipelines, Kubernetes manifests, Helm charts, GitOps configs, or Ansible playbooks — no application source code. Only engineering maturity (ENG-Q1 through ENG-Q6) and foundational auth (AUTH-Q1 through AUTH-Q3) apply. ENG questions evaluate IaC governance, CI/CD pipelines, rollback capability, test coverage, encryption config, and network policies — all present in deployment config repos. AUTH-Q1 through AUTH-Q3 evaluate machine identity, scoped permissions, and action-level authorization defined in deployment manifests.
- **`library`** — Package repositories with source code but no deployable entry point (no Dockerfile, no IaC, no main()). ENG-Q1 through ENG-Q6 are N/A because libraries have no deployment infrastructure, no CI/CD deployment pipeline, no rollback capability, and no encryption-at-rest or network policy configuration. All other questions apply because libraries expose APIs, handle auth, manage state, and process data that agents may consume through dependent applications.
- **`monorepo`** — Repositories containing multiple independent services. All 49 questions apply, assessed per-service within the repo. Each service directory is evaluated independently against the full question set.

### N/A Display Format

When a question is N/A for the detected `repo_type`, record it as:

| Field | Value |
|-------|-------|
| **Severity** | N/A |
| **Finding** | This is a `{repo_type}` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |

Replace `{repo_type}` with the actual resolved repo type value (e.g., "This is a `infrastructure-only` repository. This question does not apply.").

### N/A Exclusion Rules

N/A questions are **excluded** from the following:

1. **BLOCKER count** — N/A questions do not count as BLOCKERs, even if the question's default severity is BLOCKER.
2. **RISK count** — N/A questions do not count as RISKs.
3. **INFO count** — N/A questions do not count as INFOs.
4. **Readiness profile determination** — Only non-N/A questions with BLOCKER or RISK severity are used to determine the readiness profile (Agent-Ready, Pilot-Ready, Remediation Required, Not Agent-Integrable). N/A questions have no effect on the profile.

### N/A Inclusion Rule

All 49 questions **must appear** in the report output. N/A questions are listed in the detailed findings section using the N/A display format above — they are **not omitted** from the report. This ensures the report is a complete record of all 49 questions regardless of repo type, and makes it clear which questions were skipped and why.

### How to Apply the N/A Mapping

For each evaluation step (Steps 2–9), before evaluating a question:

1. Check whether the question ID appears in the N/A mapping for the resolved `repo_type`.
2. If the question **is** in the N/A set: skip evaluation, record the question using the N/A display format, and move to the next question.
3. If the question **is not** in the N/A set: evaluate the question normally against the repository evidence.
4. If **all** questions in a section are N/A for the detected repo type, skip the section evaluation entirely but still list all questions from that section in the report using the N/A display format.


### Step 2: API Surface and Interface Design (10 questions)

Evaluate the application's API surface — the integration layer that agents will call. APIs are the minimum viable integration surface for agent tools. This section assesses whether the APIs are documented, machine-readable, well-structured, versioned, and operationally ready for autonomous consumption.

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

#### API-Q2: Machine-Readable API Specification — RISK

**Question:** Is there an OpenAPI, AsyncAPI, GraphQL schema, or equivalent machine-readable specification available and kept current with the implementation?

**Why it matters:** Agent frameworks use machine-readable specs to generate tool definitions automatically. Without one, every integration requires manual tool authoring that drifts from actual behavior. Classified as RISK (not BLOCKER) because GraphQL schemas, Smithy models, and well-documented SDKs serve the same purpose — the real blocker is no machine-readable interface at all (API-Q1).

**Look for:**
- OpenAPI/Swagger files (`openapi.yaml`, `openapi.json`, `swagger.yaml`, `swagger.json`)
- AsyncAPI specifications
- GraphQL schema files (`.graphql`, `.gql`)
- Smithy models (`.smithy`)
- Check: Is the spec auto-generated from annotations (preferred) or manually maintained? When was it last updated relative to the last API change?

---

#### API-Q3: Structured Error Responses — RISK

**Question:** Do API responses include structured error codes and machine-readable error bodies — not just HTTP status codes?

**Why it matters:** Agents need to distinguish retriable errors (timeout, rate limit) from terminal errors (invalid input, permission denied). A 500 with no body forces agents to guess.

**Look for:**
- Error response structures in code (error code, error message, retryable boolean or category)
- Consistent error response format across endpoints
- Minimum: error code, error message, and a retryable boolean or category

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

#### API-Q5: API Versioning and Deprecation — RISK

**Question:** Are API contracts versioned, and is there a deprecation policy that includes downstream notification?

**Why it matters:** Agent tool schemas break silently when APIs change without notice. Every breaking change requires updating tool definitions and revalidating agent behavior.

**Look for:**
- `/v1/`, `/v2/` URL patterns
- `Accept-Version` headers
- Versioning annotations
- Changelog files
- Deprecation notices in API docs

---

#### API-Q6: Structured Response Format — INFO

**Question:** What is the response format from service APIs? Structured JSON? XML? Binary?

**Why it matters:** LLMs consume text-based formats effectively. Complex XML or binary formats require extra parsing logic. Well-documented JSON APIs can be exposed as agent tools with minimal adaptation.

**Look for:**
- Response serialization in code
- Content-type headers
- Protobuf/Thrift definitions
- XML marshaling
- JSON serialization libraries

---

#### API-Q7: Asynchronous Operation Support — RISK

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

#### API-Q8: Event Emission for State Changes — INFO

**Question:** Can the system emit events or webhooks for meaningful state changes that agents may need to react to — such as record updates, status transitions, or completion of long-running operations?

**Why it matters:** Request/response agents are reactive. Event-driven patterns unlock proactive agents that respond to real-world changes without polling. INFO for now because most initial deployments are request-driven, but becomes RISK when the use case requires time-sensitive reaction.

**Look for:**
- Webhook endpoints
- SNS/EventBridge/SQS integration
- Kafka topics
- CDC pipelines

---

#### API-Q9: Rate Limit Documentation and Headers — INFO

**Question:** Are API rate limits documented, and does the application return rate limit headers (X-RateLimit-Remaining, Retry-After)?

**Why it matters:** Agents call endpoints at machine speed without rate limit awareness. Undocumented limits cause unpredictable failures. Rate limit headers allow agents to self-throttle.

**Look for:**
- API Gateway throttle settings
- WAF rate rules
- Rate limiting middleware
- `X-RateLimit-Remaining` headers in response code
- `aws_api_gateway_usage_plan` in IaC

---

#### API-Q10: API Latency Profile — INFO

**Question:** What is the P95 response time for the APIs agents will consume?

**Why it matters:** An agent calling 5 tools sequentially, each with a 5-second P95, creates a 25-second minimum response time. This shapes whether to use sync or async patterns.

**Look for:**
- Performance benchmarks or load test results
- CloudWatch latency metrics
- APM dashboards
- Benchmark: Sub-second P95 ideal. 1–5s acceptable with caching. Over 5s should use async (API-Q7).


### Step 3: Authentication, Authorization, and Identity (8 questions)

Evaluate the application's authentication, authorization, and identity controls — the security layer that determines who (or what) can call the system and what they can do. Agents cannot use human credentials, so the system must support machine identity, scoped permissions, and immutable audit trails.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### AUTH-Q1: Machine Identity Authentication — BLOCKER

**Question:** Does the application support service account or machine identity authentication (client credentials OAuth 2.0, API key with principal attribution, or mTLS), and can the authenticated principal be attributed in audit logs?

**Why it matters:** Agents cannot use human credentials. The application must distinguish which agent made a call — a generic service account with no attribution is insufficient for audit and forensics.

**Look for:**
- OAuth2 client credentials flow
- API key authentication with principal attribution
- mTLS configuration
- Service account definitions
- Cognito app clients
- API Gateway authorizers
- Check audit logs for agent identity fields

---

#### AUTH-Q2: Scoped Permissions (Least Privilege) — RISK

**Question:** Does the authorization model support scoped permissions — an agent identity can be granted read-only access to specific resources without inheriting broader privileges?

**Why it matters:** Agents under overly broad permissions create blast radius risk. Least-privilege is critical, though enforcement can happen at the platform layer (API Gateway, IAM policies) if the app itself is coarse-grained.

**Look for:**
- IAM policies with specific actions per resource vs wildcards (`Action: "*"`, `Resource: "*"`)
- Role-per-service vs shared roles
- API Gateway resource policies
- Condition keys in IAM policies

---

#### AUTH-Q3: Action-Level Authorization — RISK

**Question:** Can the application enforce action-level authorization — allowing an agent to read records but not delete them, even within the same resource type?

**Why it matters:** Action-level authorization (ABAC or fine-grained RBAC) is required for agents executing multi-step workflows with mixed read/write operations.

**Look for:**
- ABAC policies
- Fine-grained RBAC definitions
- Permission matrices in code
- Action-level checks in middleware (`canRead`, `canWrite`, `canDelete`)
- API Gateway method-level authorization

---

#### AUTH-Q4: Identity Propagation — RISK

**Question:** Does the system support token exchange mechanisms (JWT/OAuth, on-behalf-of flows) that carry the originating user context end-to-end through service calls?

**Why it matters:** Without technical identity propagation, the system either cannot personalize responses per user or silently exposes all user data to every agent call.

**Look for:**
- JWT parsing middleware
- OAuth2 on-behalf-of flows
- Token exchange patterns
- Cognito/Okta integration
- User context headers (`X-User-Id`, `Authorization Bearer`) passed through service calls

---

#### AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User — RISK

**Question:** Can the system distinguish between an agent acting under its own service identity and an agent acting on behalf of a specific human user? Are these two modes logged and authorized separately?

**Why it matters:** These are fundamentally different access patterns. An agent acting as itself should have tightly scoped permissions. An agent acting on behalf of a user should be bounded by that user's permissions, not the agent's broader service account. Conflating the two is a common source of privilege escalation.

**Look for:**
- Separate IAM roles or API keys for agent-as-self vs agent-on-behalf-of-user
- Different auth flows for service-to-service vs user-delegated calls
- Audit log fields distinguishing the two modes

---

#### AUTH-Q6: Credential Management — RISK

**Question:** Are credentials managed through a secrets management system (AWS Secrets Manager, HashiCorp Vault) with rotation, or are they embedded in code, environment variables, or configuration files?

**Why it matters:** Hardcoded credentials are a security vulnerability — a prompt injection attack or agent bug could leak them. Assess whether secret rotation breaks agent continuity.

**Look for:**
- `aws_secretsmanager_*` in IaC
- Vault client imports
- Hardcoded patterns (`password=`, `secret=`, `api_key=` in code)
- `.env` files committed to git
- Environment variables with credential values in docker-compose or task definitions

---

#### AUTH-Q7: Immutable Audit Logging — BLOCKER ⚡ (Conditional)

**Question:** Does the application log the authenticated principal for every write operation, and is that log immutable and tamper-evident?

**⚡ Conditional BLOCKER:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **BLOCKER**. For regulated data contexts (EU AI Act, HIPAA, SOX), immutable audit trails are a compliance requirement. Write-enabled agents must have full audit attribution.
- **When `agent_scope` is `"read-only"`:** Evaluate as **RISK**. Audit logging is still important for read-only agents but is not a deployment blocker.

**Why it matters:** Audit trails must identify whether an action was taken by a human or an agent, and which specific agent instance. Without immutable logs, you cannot prove compliance or conduct forensics.

**Look for:**
- `aws_cloudtrail` in IaC
- CloudTrail log file validation enabled
- S3 bucket with object lock for logs
- CloudWatch log retention policies
- Immutable log storage configuration

---

#### AUTH-Q8: Agent Identity Suspension — RISK

**Question:** Can individual agent identities be suspended or revoked immediately if anomalous behavior is detected, without taking down the broader platform?

**Why it matters:** The ability to isolate a misbehaving agent without disrupting other agents or users is a fundamental operational requirement.

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
- **When `agent_scope` is `"read-only"`:** Evaluate as **RISK**. Read-only agents do not execute write workflows, but compensation capability is still relevant for system maturity.

**Why it matters:** Agents executing a 5-step workflow may succeed on steps 1–4 and fail on step 5. Without rollback or compensation logic, the application is left in a partial state.

**Look for:**
- Saga pattern
- Two-phase commit
- Explicit undo endpoints
- Compensating transactions
- Step Functions with error handling and rollback states

---

#### STATE-Q2: Queryable Current State — RISK

**Question:** Does the application expose its current state in a queryable form that an agent can inspect before taking action?

**Why it matters:** Agents need to read current state before deciding next steps. Write-only or event-only interfaces force agents to maintain external state, introducing synchronization risk.

**Look for:**
- GET endpoints for resource state
- Status query APIs
- Read-before-write patterns in code
- State machine status fields in database schemas

---

#### STATE-Q3: Concurrency Controls — RISK ⚡ (Scope-Calibrated)

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

#### STATE-Q4: Circuit Breakers and Resilience — RISK

**Question:** Does the target system implement circuit breakers, retry logic, and timeout configurations for its own external dependency calls?

**Why it matters:** When an agent calls the target system, that request may trigger cascading calls to the system's own dependencies. Circuit breakers prevent the target system from becoming a bottleneck that cascades failures back to the agent.

**Look for:**
- Resilience4j, Polly, retry decorators
- Exponential backoff
- `@CircuitBreaker` annotations
- Timeout configurations on HTTP clients

---

#### STATE-Q5: Rate Limiting and Throttling — RISK

**Question:** Are rate limits enforced at the API layer to prevent runaway agent loops from overwhelming the application?

**Why it matters:** A runaway agent loop can DDoS your own services at machine speed. Rate limiting prevents agent bugs from taking down production.

**Look for:**
- API Gateway throttling config
- WAF rate rules
- Application-level rate limiting middleware (`express-rate-limit`, `django-ratelimit`)
- `aws_api_gateway_usage_plan` in IaC

---

#### STATE-Q6: Blast Radius and Transaction Limits — RISK ⚡ (Scope-Calibrated)

**Question:** Can the system enforce configurable limits on agent-initiated actions — such as maximum records modified per run, maximum spend per hour, or maximum delete operations per session — independently of general rate limits?

**⚡ Scope-Calibrated:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **RISK**. Write-enabled agents can execute correct-but-catastrophic logic at machine speed. Transaction limits define the maximum blast radius of an agent error.
- **When `agent_scope` is `"read-only"`:** Evaluate as **INFO**. Read-only agents cannot modify records, trigger spend, or delete data. Transaction limits for write operations are informational only — relevant for future scope expansion planning.

**Why it matters:** Rate limits (STATE-Q5) protect the system from traffic overload. Transaction limits protect the business from the consequences of an agent executing correct-but-catastrophic logic — deleting 10,000 records instead of 100, or issuing $50,000 in refunds in a loop. These limits define the maximum blast radius of an agent error.

**Look for:**
- Configurable transaction limits per agent identity
- Examples: `max_refunds_per_hour=50`, `max_records_per_bulk_operation=500`, `max_spend_per_session=$1000`
- Configurable per agent identity, not just per API endpoint

---

#### STATE-Q7: Infrastructure Capacity for Agent Traffic — RISK

**Question:** Is the backend infrastructure sized and tested for the unpredictable, exploratory traffic patterns that agents generate?

**Why it matters:** APIs designed for human-paced interaction are load-tested for known traffic profiles. Agents don't respect those assumptions — they explore, retry, and fan out. Agent-induced load can starve unrelated systems sharing the backend.

**Look for:**
- Load test results or configurations
- Auto-scaling policies
- Capacity planning documentation
- Circuit breakers isolating agent traffic from other consumers


### Step 5: Human-in-the-Loop and Approval Workflows (3 questions)

Evaluate whether the application supports human oversight for high-stakes agent operations. Agents should not commit irreversible actions autonomously for high-risk operations — draft states, approval gates, and sandbox environments provide defense in depth.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### HITL-Q1: Draft/Pending State — RISK ⚡ (Scope-Calibrated)

**Question:** Does the application have the concept of a pending or draft state that an agent can write to before a human approves and commits?

**⚡ Scope-Calibrated:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **RISK**. Write-enabled agents should not commit irreversible actions autonomously for high-stakes operations. Draft states let agents propose and humans confirm.
- **When `agent_scope` is `"read-only"`:** Evaluate as **INFO**. Read-only agents do not make state changes, so draft/pending states are informational only — relevant for future scope expansion planning.

**Why it matters:** Agents should not commit irreversible actions autonomously for high-stakes operations. Draft states let agents propose and humans confirm.

**Look for:**
- Draft/pending status fields in database schemas
- Approval workflow endpoints
- Two-step commit patterns (create-then-confirm)
- Status-based state machines

---

#### HITL-Q2: Configurable Approval Gates — RISK ⚡ (Scope-Calibrated)

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

#### HITL-Q3: Sandbox/Staging Environment — RISK

**Question:** Is there a sandbox or staging environment with production-equivalent data shape that agents can use for testing without risk to live systems?

**Why it matters:** Agents must be testable against realistic conditions before production promotion. Without a staging environment, the first time you discover an agent bug is in production.

**Look for:**
- Separate environment configurations (staging, sandbox)
- Docker-compose for local testing
- Seed data scripts
- Synthetic data generators
- Environment-specific IaC


### Step 6: Data Accessibility and Quality (8 questions)

Evaluate the data layer that agents will access — classification, residency, query capabilities, quality, and privacy controls. Agents process data at machine speed, so unclassified sensitive data, unbounded queries, and PII leakage into logs create regulatory and operational risk at scale.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### DATA-Q1: Sensitive Data Classification — BLOCKER

**Question:** Is sensitive data (PII, PHI, financial records, credentials) classified and tagged at the field level, and are there controls preventing an agent from retrieving it without explicit authorization?

**Why it matters:** Unclassified sensitive data in a retrieval pipeline is a regulatory and reputational risk. Classification must happen before agents get read access.

**Look for:**
- Data classification tags in IaC (`aws_s3_bucket` tags, DynamoDB table tags)
- Field-level encryption
- Column-level access controls
- PII detection tools (Macie)
- Data classification policies in documentation

---

#### DATA-Q2: Data Residency and Sovereignty — BLOCKER ⚡ (Conditional)

**Question:** Is the data subject to residency or sovereignty requirements that would restrict an agent from transmitting it to an LLM provider in a different region or jurisdiction?

**⚡ Conditional BLOCKER:**
- **When `agent_scope` is `"write-enabled"`:** Evaluate as **BLOCKER**. For regulated data (GDPR, LGPD, HIPAA, sector-specific), an agent sending regulated data to an LLM endpoint in another region may create a legal violation.
- **When `agent_scope` is `"read-only"`:** Evaluate as **RISK**. Data residency is still relevant for read-only agents but the risk profile is lower when no data modification occurs.

**Why it matters:** An agent sending regulated data to an LLM endpoint in another region may create a legal violation. The data residency constraints are properties of the data the system holds.

**Look for:**
- Data residency requirements in documentation
- GDPR/LGPD compliance references
- Region-specific data storage configurations
- Cross-region replication settings
- Data sovereignty policies

---

#### DATA-Q3: Selective Query Support — RISK

**Question:** Can data be queried with filters, pagination, and sorting that limit result set size to what an agent actually needs?

**Why it matters:** Agents retrieving unbounded result sets exhaust LLM context windows and increase cost.

**Look for:**
- Pagination parameters in API endpoints (`limit`, `offset`, `cursor`)
- Filter query parameters
- Sorting options
- GraphQL field selection
- Result size limits in API documentation

---

#### DATA-Q4: System of Record Designations — RISK

**Question:** Are there authoritative system-of-record designations for key entities, and is there a master data management process that resolves conflicts across systems?

**Why it matters:** Agents reasoning across multiple systems will encounter conflicting records. Without a golden record, decisions will be inconsistent.

**Look for:**
- Master data management references
- System-of-record designations in documentation
- Data ownership definitions
- Conflict resolution logic
- Golden record patterns

---

#### DATA-Q5: Reliable Timestamps — RISK

**Question:** Does the data include reliable, timezone-normalized timestamps for creation, last update, and source event time?

**Why it matters:** Agents performing time-sensitive reasoning depend on accurate temporal data. Missing or unreliable timestamps cause silent errors.

**Look for:**
- `created_at`, `updated_at`, `event_time` fields in database schemas
- Timezone handling (UTC storage)
- Timestamp format consistency
- NTP synchronization configuration

---

#### DATA-Q6: Data Freshness Signaling — RISK

**Question:** Can the system indicate whether data returned to an agent is current, stale, cached, or eventually consistent? Does it expose cache age, last-refreshed timestamps, or consistency guarantees at the response level?

**Why it matters:** Agents make consequential decisions fast based on data retrieved seconds ago. If the system cannot signal that data is cached or eventually consistent, the agent has no way to know whether it is reasoning on the current state.

**Look for:**
- `Cache-Control` headers
- `X-Data-Age` headers
- `last_refreshed` field
- `consistency_level` field (strong / eventual / cached)

---

#### DATA-Q7: PII Redaction in Logs — RISK

**Question:** Is PII redacted from logs, error messages, and observability data?

**Why it matters:** Agents process customer PII. If PII leaks into logs or LLM prompt/response pairs, it becomes a compliance violation.

**Look for:**
- Log scrubbing middleware
- PII masking libraries
- CloudWatch log filters
- Amazon Macie integration
- Regex patterns for PII in logging utilities

---

#### DATA-Q8: Data Quality Awareness — INFO

**Question:** Is there a known data quality score or completeness metric for this dataset?

**Why it matters:** Agents acting on incomplete or stale data propagate errors faster than human workflows. Planning input, not a deployment blocker.

**Look for:**
- Data quality dashboards
- Data profiling reports
- Null rate monitoring
- Duplicate detection logic
- Data freshness SLAs
- Data quality metrics in observability


### Step 7: Discoverability and Semantic Readiness (4 questions)

Evaluate whether the system's data and APIs are discoverable and semantically meaningful — can an agent (or the team building agent tools) understand what data exists, what it means, and where it came from? This section accelerates tool definition and improves agent reasoning quality.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### DISC-Q1: Schema Documentation and Versioning — RISK

**Question:** Are data schemas documented, versioned, and accessible?

**Why it matters:** Agents need to understand data structures. Schema changes without versioning break agent queries silently.

**Look for:**
- JSON Schema files
- Avro/Protobuf schemas
- Database migration files
- Schema registry
- OpenAPI schema definitions

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

#### DISC-Q4: Data Lineage — INFO

**Question:** Is there a lineage record showing where each data element originated and how it was transformed?

**Why it matters:** When an agent produces incorrect output due to bad data, lineage is how you trace it.

**Look for:**
- Data lineage tools (AWS Glue DataBrew, Apache Atlas)
- ETL pipeline documentation
- Data flow diagrams
- Transformation logs
- Source-to-target mappings


### Step 8: Observability of Target Systems (3 questions)

Evaluate the observability of the target systems that agents will call — distributed tracing, alerting, and business outcome metrics. When an agent-initiated request fails, the target system's observability determines whether you can diagnose the problem or are flying blind.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### OBS-Q1: Distributed Tracing and Structured Logging — RISK

**Question:** Does the application support distributed tracing (X-Ray, OpenTelemetry) with trace ID propagation, and are logs structured (JSON) with correlation IDs linking all entries for a single request?

**Why it matters:** These two controls serve the same diagnostic purpose — reconstructing what happened inside the target system when an agent-initiated request fails. Both must be present to make agent-initiated failures debuggable.

**Look for:**
- OpenTelemetry SDK
- X-Ray instrumentation
- `traceparent` header propagation
- JSON logs
- `request_id` or `correlation_id` field

---

#### OBS-Q2: Alerting on Error Rates and Latency — RISK

**Question:** Are there alerting thresholds configured for error rates and latency on the APIs agents will consume?

**Why it matters:** Target system degradation is felt immediately by agents. Alerting lets you detect problems before agents start cascading failures.

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


### Step 9: Engineering and Deployment Maturity (6 questions)

Evaluate the engineering and deployment maturity of the target system — infrastructure governance, CI/CD with contract testing, rollback capability, test coverage, encryption, and network policies. These controls determine whether the system can be safely and reliably operated as an agent integration surface.

Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If a question is N/A, record it in the N/A display format and skip evaluation.

---

#### ENG-Q1: Infrastructure Governance for Agent-Facing Surface — RISK

**Question:** Is the infrastructure exposing the target system to agents — API gateways, IAM roles, secrets, network configurations — defined as code, subject to peer review before changes, and monitored for drift?

**Why it matters:** The integration surface is a high-value attack surface. All three controls — IaC definition, change review, and drift detection — must be present together for this surface to be trustworthy.

**Look for:**
- Sub-checks: (1) Integration surface defined as IaC? (2) Changes subject to automated plan review + peer review? (3) Drift detection active?
- Terraform, CloudFormation, or CDK definitions for API Gateway, IAM, secrets, networking
- PR/CR review requirements on IaC changes
- AWS Config rules or drift detection configuration

---

#### ENG-Q2: CI/CD with API Contract Testing — RISK

**Question:** Does the target system have a CI/CD pipeline that includes automated testing of agent-facing APIs and the ability to detect API-breaking changes before production?

**Why it matters:** The agentic concern is not "does CI/CD exist" but "can API contract changes be caught before agents are affected."

**Look for:**
- API contract tests in CI pipeline
- Consumer-driven contract testing (Pact)
- OpenAPI spec validation in build
- Schema comparison tools
- Breaking change detection

---

#### ENG-Q3: Rollback Capability — RISK

**Question:** Can the target system's deployment be rolled back to the previous known-good state if a change breaks agent-facing APIs? (Target: within 15–30 minutes.)

**Why it matters:** A broken API that agents depend on leaves agents unable to function. The intent — fast, reliable rollback — matters more than the exact time threshold. Organizations with canary + circuit breaker patterns achieve safe recovery.

**Look for:**
- Blue/green deployment config
- CodeDeploy rollback triggers
- Helm rollback
- Feature flags
- Canary deployment with automatic rollback
- Traffic shifting at API Gateway or ALB

---

#### ENG-Q4: API Test Coverage — RISK

**Question:** Are there automated tests for the APIs agents will consume — validating input handling, output format, error responses, and edge cases — running in CI?

**Why it matters:** APIs are the contract between agent and target system. If behavior changes without test coverage catching it, agents reason incorrectly.

**Look for:**
- API test suites (Postman/Newman collections, pytest API tests, REST Assured)
- Contract tests
- Integration test directories
- API test steps in CI pipeline configuration

---

#### ENG-Q5: Encryption at Rest for Agent-Accessible Data — RISK

**Question:** Is data encrypted at rest (KMS) for sensitive information that agents will access?

**Why it matters:** Agents access data stores containing PII and business-sensitive information. Unencrypted data at rest means a breach exposes everything the agent can access.

**Look for:**
- `kms_key_id` on S3/RDS/DynamoDB/EBS
- Customer-managed KMS keys
- Encryption config in IaC

---

#### ENG-Q6: Cross-Origin and Network Policies — RISK

**Question:** Are CORS policies and network security configurations (security groups, firewall rules, API gateway settings) documented and discoverable, regardless of whether they are defined in application code, infrastructure-as-code repos, or centralized configuration systems?

**Why it matters:** Network policies are a defense-in-depth control that restricts which pods or services can communicate at the network layer. While important for overall security posture, they are an enforcement mechanism for authorization decisions that should be made at the application or service mesh layer (AUTH-Q1, AUTH-Q3). If authentication and authorization are properly implemented, network policies provide a secondary defense layer rather than a primary agent safety gate. CORS is a browser-enforced mechanism irrelevant to machine-to-machine agent traffic. Classified as RISK (not BLOCKER) because the absence of network policies does not directly prevent safe agent integration when identity and authorization controls are in place — it reduces defense depth.

**Look for:**
- CORS configuration in API Gateway or application middleware
- Security group rules in IaC
- Firewall rules
- Network policies in Kubernetes
- API gateway access policies
- WAF rules


## Report Template

After evaluating all 49 questions across Steps 2–9, compile the findings into a structured Markdown report. Save the report as `{repo-name}-ara-report.md` in the repository's output directory.

Create the report file with exactly this structure. Every section is required. All 49 questions must appear in the detailed findings — N/A questions are listed using the N/A display format, not omitted.

### Report Metadata Header

```markdown
# Agentic Readiness Assessment Report
**Target**: <repository path>
**Date**: <date>
**Assessed by**: AWS Transform Custom — Agentic Readiness Assessment
**Repository Type**: <resolved repo_type>
**Agent Scope**: <resolved agent_scope>
**Priority**: <priority if provided, otherwise omit this line>
**Tags**: <tags if provided, otherwise omit this line>
**Context**: <context if provided, otherwise omit this line>
```

If `repo_type` was defaulted due to an unrecognized value, include a warning line:
```markdown
**Warning**: Unrecognized repo_type '<original value>', defaulted to 'application'.
```

---

### Readiness Profile Determination

Determine the readiness profile using the BLOCKER and RISK counts from non-N/A questions only. N/A questions are excluded from all counts and have no effect on the profile.

| Readiness Profile | Blockers | Risks | Recommendation | Deployment Gate |
|-------------------|----------|-------|----------------|-----------------|
| **Agent-Ready** | 0 | 0–2 | Broad deployment | Cleared for autonomous operation. Instrument observability. Define scope explicitly. Run controlled pilot first. |
| **Pilot-Ready** | 0 | 3–5 | Narrow pilot only | Supervised pilot with: (1) human approval gates on irreversible actions, (2) agent limited to low-blast-radius operations, (3) compensating controls for each open RISK, (4) remediation timeline before expanding scope. |
| **Remediation Required** | 1–2 | Any | Remediate first | Resolve all blockers before any agent deployment — including pilots. Estimated runway: 60–180 days. |
| **Not Agent-Integrable** | 3+ | Any | Deferred or descoped | Exclude from agent toolset or plan major remediation before re-evaluation. |

**Rules:**
1. Count only non-N/A questions with severity BLOCKER → `blocker_count`.
2. Count only non-N/A questions with severity RISK → `risk_count`.
3. If `blocker_count >= 3` → **Not Agent-Integrable**.
4. If `blocker_count` is 1 or 2 → **Remediation Required** (risk_count is irrelevant).
5. If `blocker_count == 0` and `risk_count >= 6` → **Pilot-Ready** (treat 6+ unmitigated risks same as 3–5 for gating purposes — narrow pilot only).
6. If `blocker_count == 0` and `3 <= risk_count <= 5` → **Pilot-Ready**.
7. If `blocker_count == 0` and `risk_count <= 2` → **Agent-Ready**.

Display the readiness profile in the report:

```markdown
---

## Readiness Profile: <profile name>

**BLOCKERs**: <blocker_count> | **RISKs**: <risk_count> | **INFOs**: <info_count>

<Deployment gate description from the table above.>
```

---

### Summary Counts

Display the severity distribution for all non-N/A questions. N/A questions are excluded from these counts entirely.

```markdown
## Summary

| Severity | Count |
|----------|-------|
| BLOCKER | <count> |
| RISK | <count> |
| INFO | <count> |
| N/A | <count> |
| **Total** | **49** |

**Questions Evaluated**: <49 - N/A count>
**Questions N/A (repo_type: <repo_type>)**: <N/A count>
```

---

### BLOCKERs Section

List all questions that received a BLOCKER severity (including conditional BLOCKERs that resolved to BLOCKER based on `agent_scope`). For each BLOCKER, include remediation guidance.

If there are no BLOCKERs, display: "No BLOCKERs identified."

```markdown
## BLOCKERs — Must Resolve Before Agent Deployment

### <question_id>: <question topic>

- **Severity**: BLOCKER
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing or non-compliant>
- **Remediation**:
  - **Immediate**: <first concrete step to resolve this blocker>
  - **Target State**: <what "resolved" looks like>
  - **Estimated Effort**: <Low / Medium / High>
  - **Dependencies**: <other blockers or risks that interact with this one, or "None">
- **Evidence**: <specific files cited>

<Repeat for each BLOCKER question.>
```

**Remediation Prioritization Guidance:**

There is no universal remediation order — it depends on the use case, the blockers found, and the organization's constraints. However, the following principles apply:

- **Resolve BLOCKERs first.** No agent deployment (including pilots) should proceed with open BLOCKERs. Start with whichever blocker is fastest to resolve to unblock a scoped pilot.
- **Identity before data access.** If both identity (AUTH-Q1) and data classification (DATA-Q1) are blockers, fix identity first — you cannot enforce data access controls without knowing who is calling.
- **Read-only before write-enabled.** If write-operation blockers (API-Q4, STATE-Q1) are present, consider scoping the initial agent to read-only operations while remediating write safety. This unblocks value faster.

---

### RISKs Section

List all questions that received a RISK severity. For each RISK, include compensating control options that allow a scoped pilot to proceed while the risk is remediated.

If there are no RISKs, display: "No RISKs identified."

```markdown
## RISKs — Proceed with Compensating Controls

### <question_id>: <question topic>

- **Severity**: RISK
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing or incomplete>
- **Compensating Controls**:
  - <option 1: a control that mitigates this risk for a scoped pilot>
  - <option 2: an alternative mitigation approach>
- **Remediation Timeline**: <suggested timeline to fully resolve — e.g., "30–60 days">
- **Recommendation**: <specific next step to remediate>
- **Evidence**: <specific files cited>

<Repeat for each RISK question.>
```

**RISK Prioritization Guidance:**

- RISKs are prioritized by use case. A RISK that is irrelevant to the planned agent scope can be deferred. A RISK that directly affects the planned scope should be treated with urgency.
- Compensating controls buy time, not exemptions. A RISK mitigated by a compensating control (e.g., human-in-the-loop gate) is acceptable for a pilot but must be remediated before expanding scope.

---

### INFOs Section

List all questions that received an INFO severity. INFOs are not deployment gates — they shape architecture decisions and agent design.

If there are no INFOs, display: "No INFOs identified."

```markdown
## INFOs — Architecture and Design Inputs

### <question_id>: <question topic>

- **Severity**: INFO
- **Finding**: <what was observed, with specific file and resource references>
- **Implication**: <how this shapes agent design or architecture decisions>
- **Recommendation**: <optional improvement or consideration>
- **Evidence**: <specific files cited>

<Repeat for each INFO question.>
```

---

### Detailed Findings — All 49 Questions

List every question from all 8 sections in order (API-Q1 through ENG-Q6). This section is the complete record of the assessment. All 49 questions must appear — including N/A questions.

```markdown
## Detailed Findings

### 01 — API Surface and Interface Design

#### API-Q1: Documented API Interface
- **Severity**: <BLOCKER / RISK / INFO / N/A>
- **Finding**: <what was observed, with specific file and resource references>
- **Gap**: <what is missing, or "N/A">
- **Recommendation**: <specific next step, or "N/A">
- **Evidence**: <files cited, or "N/A">

#### API-Q2: Machine-Readable API Specification
- **Severity**: <BLOCKER / RISK / INFO / N/A>
- **Finding**: <what was observed>
- **Gap**: <what is missing, or "N/A">
- **Recommendation**: <specific next step, or "N/A">
- **Evidence**: <files cited, or "N/A">

<Continue for API-Q3 through API-Q10>

### 02 — Authentication, Authorization, and Identity

#### AUTH-Q1: Machine Identity Authentication
- **Severity**: <BLOCKER / RISK / INFO / N/A>
- **Finding**: <what was observed>
- **Gap**: <what is missing, or "N/A">
- **Recommendation**: <specific next step, or "N/A">
- **Evidence**: <files cited, or "N/A">

<Continue for AUTH-Q2 through AUTH-Q8>

### 03 — State Management and Transactional Integrity

<STATE-Q1 through STATE-Q7 in the same format>

### 04 — Human-in-the-Loop and Approval Workflows

<HITL-Q1 through HITL-Q3 in the same format>

### 05 — Data Accessibility and Quality

<DATA-Q1 through DATA-Q8 in the same format>

### 06 — Discoverability and Semantic Readiness

<DISC-Q1 through DISC-Q4 in the same format>

### 07 — Observability of Target Systems

<OBS-Q1 through OBS-Q3 in the same format>

### 08 — Engineering and Deployment Maturity

<ENG-Q1 through ENG-Q6 in the same format>
```

**For N/A questions**, use the N/A display format defined in the N/A Mapping section:

```markdown
#### <question_id>: <question topic>
- **Severity**: N/A
- **Finding**: This is a `<repo_type>` repository. This question does not apply.
- **Gap**: N/A
- **Recommendation**: N/A
- **Evidence**: N/A
```

**For conditional BLOCKER (⚡) questions** (API-Q4, STATE-Q1, AUTH-Q7, DATA-Q2), include the resolved severity based on `agent_scope`:

```markdown
#### <question_id>: <question topic> ⚡
- **Severity**: <BLOCKER if write-enabled / INFO or RISK if read-only>
- **Conditional**: agent_scope is "<agent_scope>" — evaluated as <resolved severity>
- **Finding**: <what was observed>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>
- **Evidence**: <files cited>
```

**For scope-calibrated RISK (⚡) questions** (HITL-Q1, HITL-Q2, STATE-Q3, STATE-Q6), include the resolved severity based on `agent_scope`:

```markdown
#### <question_id>: <question topic> ⚡
- **Severity**: <RISK if write-enabled / INFO if read-only>
- **Scope-Calibrated**: agent_scope is "<agent_scope>" — evaluated as <resolved severity>
- **Finding**: <what was observed>
- **Gap**: <what is missing>
- **Recommendation**: <specific next step>
- **Evidence**: <files cited>
```

---

### Evidence Index

Compile a complete index of all files cited as evidence across the assessment. Group by file type for easy reference.

```markdown
## Evidence Index

### Infrastructure as Code
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Source Code
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### API Specifications
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### CI/CD Configurations
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Container Definitions
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Dependency Manifests
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |

### Configuration Files
| File | Questions Referenced |
|------|---------------------|
| <file path> | <question IDs that cited this file> |
```

If no files were found for a category, omit that category from the evidence index.

**Evidence Rules:**
- Every finding must cite at least one file or explicitly state "No evidence found — absence is itself a finding."
- File paths must be relative to the repository root.
- The same file may appear in multiple categories if it serves multiple purposes (e.g., a `docker-compose.yml` may be cited for both container definitions and configuration).

---

### Table of Contents

The complete report structure, for reference:

```markdown
# Agentic Readiness Assessment Report

1. Readiness Profile
2. Summary
3. BLOCKERs — Must Resolve Before Agent Deployment
4. RISKs — Proceed with Compensating Controls
5. INFOs — Architecture and Design Inputs
6. Detailed Findings
   - 01 — API Surface and Interface Design (API-Q1 through API-Q10)
   - 02 — Authentication, Authorization, and Identity (AUTH-Q1 through AUTH-Q8)
   - 03 — State Management and Transactional Integrity (STATE-Q1 through STATE-Q7)
   - 04 — Human-in-the-Loop and Approval Workflows (HITL-Q1 through HITL-Q3)
   - 05 — Data Accessibility and Quality (DATA-Q1 through DATA-Q8)
   - 06 — Discoverability and Semantic Readiness (DISC-Q1 through DISC-Q4)
   - 07 — Observability of Target Systems (OBS-Q1 through OBS-Q3)
   - 08 — Engineering and Deployment Maturity (ENG-Q1 through ENG-Q6)
7. Evidence Index
```


## Constraints and Guardrails

Strictly follow these rules at all times:

- **Read-only assessment**: Do not modify any source code, configuration, or infrastructure in the repository. Only create the output report file.
- **Be specific — cite evidence**: Always reference actual file names, resource names, and patterns found. Never write "there may be..." — state what was found or what was not found.
- **Absence is evidence**: If a search for a specific artifact finds nothing (e.g., no OpenAPI spec, no IaC files, no audit logging configuration), that absence is itself a finding. State it clearly and score accordingly.
- **Read before judging**: Do not score a question without actually reading relevant files. If relevant files have not been found yet, keep searching.
- **IaC is ground truth**: Trust IaC definitions over README descriptions. What is deployed is what is defined in the IaC.
- **Do not skip questions**: All 49 questions must be evaluated and appear in the report. Questions that are N/A for the detected `repo_type` must still appear using the N/A display format — they are listed, not omitted.
- **N/A scoring rules**: Questions scored as N/A are excluded from BLOCKER, RISK, and INFO counts and from readiness profile determination. N/A questions do not affect the readiness profile.
- **Conditional BLOCKER rules**: The 4 conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q7, DATA-Q2) must be evaluated at the severity determined by `agent_scope`. Do not override the conditional logic.
- **Scope-calibrated RISK rules**: The 4 scope-calibrated RISK questions (HITL-Q1, HITL-Q2, STATE-Q3, STATE-Q6) must be evaluated as RISK when `agent_scope` is `"write-enabled"` and as INFO when `agent_scope` is `"read-only"`. Do not override the scope calibration logic.
- **Repo type classification**: Use the `repo_type` from `additionalPlanContext`. If not provided, default to `application`. Apply the N/A mapping table exactly as defined — do not add or remove N/A mappings.
- **No goal system**: This TD does not use goals, goal_context, preferences, pathways, decomposition strategies, numeric scores, or goal-based re-weighting. If these fields appear in `additionalPlanContext`, ignore them.
- **Report completeness**: The output report must contain all required sections: metadata header, readiness profile, summary counts, BLOCKERs with remediation, RISKs with compensating controls, INFOs, detailed findings for all 49 questions, and evidence index.
