---
name: agentic-readiness-analysis
description: Evaluates whether systems are ready to be safely called by AI agents - covering APIs, identity, state management, human-in-the-loop, and observability
type: managed
---

## Name

Agentic Readiness Analysis

## Objective

Evaluate whether a repository's systems — infrastructure, applications, data, security controls, and operational practices — are safe, operable, and integrable for autonomous AI agent integration. This analysis targets the environment that agents will call or consume, not the agent itself. It answers the question: are the systems agents will interact with ready to be called safely?

The analysis serves two purposes: (1) portfolio-level telemetry — a snapshot of which systems are agent-ready, which need remediation, and where systemic gaps exist; and (2) use-case-level dependency checking — given a specific agent workflow, which target systems are blockers?

ARA is a design-time architecture review — it evaluates whether controls exist in code and configuration, not whether they are effective at runtime. It is not a penetration test or runtime security scan.

## Summary

This transformation performs a dedicated Agentic Readiness Analysis on a codebase. It scans all files in the repository to discover infrastructure-as-code, application source code, CI/CD definitions, API specifications, dependency manifests, configuration files, and container definitions. It then evaluates what it finds against 43 questions across 8 sections:

- **API** — API Surface and Interface Design (8 questions: 4 core + 4 extended)
- **AUTH** — Authentication, Authorization, and Identity (7 questions: all core)
- **STATE** — State Management and Transactional Integrity (7 questions: 3 core + 4 extended)
- **HITL** — Human-in-the-Loop and Approval Workflows (3 questions: 1 core + 2 extended)
- **DATA** — Data Accessibility and Quality (7 questions: 4 core + 3 extended)
- **DISC** — Discoverability and Semantic Readiness (3 questions: 1 core + 2 extended)
- **OBS** — Observability of Target Systems (3 questions: 2 core + 1 extended)
- **ENG** — Engineering and Deployment Maturity (5 questions: 3 core + 2 extended)

## Reference Files

This definition is split into a lean orchestration spine (this file) plus four reference files, loaded on demand at the point in the flow where each is needed. Load each file when the step below directs you to — do not skip any.

- **`references/01-scoring-model.md`** — evaluation tiers, severity model, unified severity/category display names, RISK-tier assignment, service-archetype classification, and the readiness-profile table. Load before assigning any severity or profile.
- **`references/02-question-bank.md`** — the authoritative catalog of all 43 questions (Steps 2–9), each with severity, scope-conditional resolution, and surface-flag/archetype calibration. Load after Discovery and archetype detection.
- **`references/03-report-template.md`** — the markdown report structure: metadata header, readiness-profile determination, summary counts, BLOCKER/RISK/INFO sections, detailed findings, evidence index.
- **`references/04-output-contract.md`** — the machine-readable four-artifact contract: unified per-finding field set, `ara_metadata`, `evaluations[]`, classification rules, HTML visual contract, and error handling.

## Entry Criteria

- The repository is accessible and readable at the specified path
- The repository contains files relevant to analysis (source code, IaC, API specs, CI/CD configs, dependency manifests, container definitions, or configuration files)
- Write permissions exist to create the output artifact bundle (MD, JSON, HTML, and metadata.json)
- The analysis operates in **read-only mode** — it will not modify any source code or configuration in the repository
- Stay on the current branch — this is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out.

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning the discovery scan, read the analysis context from `additionalPlanContext` to determine the repo classification, agent scope, and framing context that will shape the entire analysis.

#### 0.1 Read Analysis Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `repo_type` | enum | No | `"application"` | Repository classification. One of: `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`. Determines which questions are scored as N/A. |
| `agent_scope` | enum | No | `"read-only"` | The intended agent access level. One of: `read-only`, `write-enabled`. Determines severity of conditional BLOCKER (⚡) questions. |
| `service_archetype` | enum | No | auto-detected | Service archetype for severity calibration. One of: `stateless-utility`, `stateful-crud`, `orchestrator`, `data-gateway`, `event-processor`. If not provided, auto-detected in Step 1.6. Only applies when `repo_type` is `application`. |
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

- **`repo_type`** → `"application"` — This is the most comprehensive analysis (no questions skipped). Defaulting to `application` ensures nothing is missed when classification is unknown.
- **`agent_scope`** → `"read-only"` — This is the safer default. Conditional BLOCKER questions (⚡) are evaluated as INFO or RISK-SAFETY rather than BLOCKER, avoiding false escalation when the agent use case has not been scoped.
- **`service_archetype`** → Auto-detected in Step 1.6 based on repository analysis. If auto-detection is inconclusive, defaults to `"stateful-crud"` (the most conservative archetype — no severity downgrades beyond standard scope calibration). Only applies when `repo_type` is `application`.
- **`context`** → No default. If absent, findings and recommendations are written without additional framing.
- **`priority`** → No default. If absent, omitted from report metadata.
- **`tags`** → No default. If absent, omitted from report metadata.

If `repo_type` is present but not one of the 5 recognized values (`application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`), default to `"application"` and include a warning in the report metadata: **"Unrecognized repo_type '{value}', defaulting to application."**

#### 0.3 How Context Fields Are Used

Record the resolved values from Steps 0.1–0.2 in the analysis context. They will be used in subsequent steps as follows:

- **`repo_type`** → Used in the N/A Mapping (Step 1) to determine which questions are scored as N/A for the detected repo type. Included in the report metadata header.
- **`agent_scope`** → Used in Steps 2–9 (Evaluation) to determine the severity of conditional BLOCKER (⚡) questions: API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, and DATA-Q2. When `agent_scope` is `"write-enabled"`, these are evaluated as BLOCKERs. When `"read-only"`, they are evaluated as INFO or RISK-SAFETY. Also used to calibrate scope-sensitive RISK questions: HITL-Q1, HITL-Q2, STATE-Q3, and STATE-Q6 — these evaluate as RISK when `"write-enabled"` and downgrade to INFO when `"read-only"`. Included in the report metadata header.
- **`service_archetype`** → Used in Steps 2–9 (Evaluation) to calibrate severity for archetype-sensitive questions. When a question is calibrated to INFO for the detected archetype, it is recorded as INFO (not RISK) and does not count toward the RISK total. Calibration only downgrades severity — it never upgrades. Included in the report metadata header. Only applies when `repo_type` is `application`.
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
- Service mesh configs (Istio)

#### 1.2 Directories to Ignore

Skip the following directories during scanning — they contain installed dependencies, build artifacts, or version control internals that are not relevant to the analysis:

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

- **IaC files found** — List of Terraform, CloudFormation, CDK, Helm, Kustomize, and other IaC files with their paths. Used by: AUTH-Q1 (IAM/auth config), AUTH-Q5 (secrets in IaC), AUTH-Q6 (CloudTrail config), ENG-Q1 (IaC governance), ENG-Q5 (encryption at rest), STATE-Q5 (rate limiting in API Gateway), and others.
- **Source code files found** — List of application source files by language. Used by: API-Q1 (API endpoints in code), API-Q3 (error handling), API-Q4 (idempotency patterns), AUTH-Q2 (permission checks), STATE-Q3 (concurrency controls), STATE-Q4 (resilience patterns), and others.
- **API spec files found** — List of OpenAPI, AsyncAPI, GraphQL, and Smithy files. Used by: API-Q1 (documented interface), API-Q2 (machine-readable spec), DISC-Q1 (schema documentation).
- **CI/CD config files found** — List of pipeline definitions. Used by: ENG-Q2 (CI/CD with contract testing), ENG-Q3 (rollback capability), ENG-Q4 (API test coverage).
- **Container files found** — List of Dockerfiles and compose files. Used by: multiple infrastructure and deployment questions.
- **Dependency manifests found** — List of package manifests by ecosystem. Used by: identifying frameworks, libraries, and technology stack across multiple questions.
- **Configuration files found** — List of config files by type. Used by: AUTH-Q6 (hardcoded secrets), DATA-Q2 (data residency config), and others.
- **Notable absences** — Record what was NOT found. Absence is evidence: if no API spec files exist, that is a finding for API-Q2. If no IaC files exist, that is a finding for ENG-Q1. These absences are cited in evaluation steps.

#### 1.4 Read Discovered Files

Read all discovered files that are relevant to the analysis. Prioritize reading in this order:

1. **IaC files** — These reveal infrastructure architecture, security configuration, and deployment topology
2. **API specification files** — These reveal the integration surface agents will consume
3. **CI/CD configuration files** — These reveal deployment maturity and testing practices
4. **Dependency manifests** — These reveal technology stack, frameworks, and library choices
5. **Container definitions** — These reveal deployment packaging and runtime configuration
6. **Application source code** — These reveal implementation patterns, error handling, auth logic, and data access
7. **Configuration files** — These reveal runtime settings, environment configuration, and connection details

For large repositories, focus on files most relevant to the 43 evaluation questions. Not every source file needs to be read in full — prioritize entry points, API route definitions, authentication middleware, data access layers, and error handling patterns.

### Step 1.5: Target-System Surface Detection

Before evaluating any question, classify what agent-accessible surfaces this target system actually exposes. The severity of many ARA questions depends on whether the relevant surface exists at all — a build tool that never handles user data should not score BLOCKER for "no PII classification"; a library with no HTTP server should not score RISK-QUALITY for "no machine-readable API spec." This step records the surfaces so downstream evaluation can downgrade or N/A questions that do not apply.

Record each surface flag as `true`, `false`, or `unknown`. When `unknown`, the question evaluates normally (do not use `unknown` as a free pass — use it only when evidence is insufficient to decide).

#### Surface Flags

**`has_persistent_data_store`** — The system reads from or writes to a persistent data store that holds user or business data.

- `true` signals: database connections (SQL/NoSQL/ORM imports), DynamoDB/RDS/DocumentDB/Neptune/Timestream clients with CRUD operations, S3 buckets used for user content (not build artifacts), Redis with writes, Elasticsearch with indexing, stateful caches with user data
- `false` signals: library publishes no storage dependency, build tools only read source files, CLI/SDK wraps remote APIs without owning a data store, in-memory-only computations, reference/static data only (exchange rates, feature flags)
- Used by: DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q6

**`has_http_rpc_surface`** — The system exposes an HTTP, gRPC, or GraphQL server that accepts inbound requests.

- `true` signals: Express/Koa/Fastify/Hapi routes, Flask/FastAPI/Django URL configs, Spring `@RestController`, Go `http.HandleFunc` / gin routes, gRPC service definitions, GraphQL resolvers bound to server, AppSync resolvers, Lambda event handlers for API Gateway/ALB
- `false` signals: library only exports functions, CLI-only tool, build-time processor, event consumer with no external surface, desktop/browser-only code
- Used by: API-Q1 through API-Q8, DISC-Q1

**`has_auth_surface`** — The system has authentication or authorization enforcement points (either issues identity, validates tokens, or enforces scoped access).

- `true` signals: login/logout/token endpoints, JWT/OAuth middleware, IAM role assumption code, Cognito/Okta integration, API Gateway authorizers, route-level auth decorators, permission checks before data access
- `false` signals: library delegates auth to caller, pass-through proxy, pure computation with no access control, utility that does not touch identity
- Used by: AUTH-Q1, AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q6, AUTH-Q7

**`has_write_operations`** — The system exposes or performs write operations that mutate persistent state or trigger side effects.

- `true` signals: POST/PUT/PATCH/DELETE endpoints, state-mutating RPC methods, database writes behind the API surface, message publishing on state change, file system writes to user-owned paths
- `false` signals: read-only API, query-only GraphQL schema, library produces a value without side effects, formatter/parser with no persistence
- Used by: STATE-Q1, STATE-Q2, STATE-Q3, STATE-Q5, STATE-Q6

**`has_logging_of_user_data`** — The system logs request/response data, user identifiers, or business-entity content that could contain PII if upstream callers pass PII in.

- `true` signals: request-body logging middleware, access logs with user_id/email/customer fields, structured logs emitting entity payloads, error handlers printing full request context, telemetry that forwards user data
- `false` signals: library only emits internal diagnostic logs (no user fields), logs are build-time only, structured logging explicitly excludes user fields via allowlist
- Used by: DATA-Q6

#### Outputs

Record the five surface flags in the report metadata header alongside `repo_type` and `service_archetype`:

```
- **Surface flags**:
  - has_persistent_data_store: true | false | unknown
  - has_http_rpc_surface: true | false | unknown
  - has_auth_surface: true | false | unknown
  - has_write_operations: true | false | unknown
  - has_logging_of_user_data: true | false | unknown
```

These flags feed the N/A / INFO downgrade decisions in Steps 2–9. When a question's evaluation block states "if `has_X_surface` is `false`, record as INFO and skip," obey that instruction.

#### Archetype Override for Dev-Library-Applications

Some repositories classify as `application` (have source + entry point) but function as libraries, CLIs, build tools, or frontend scaffolds — examples: build orchestration tools, SDK mocks, CLI utilities, Angular/React admin templates, IaC framework plugins. For these, the N/A mapping of `application` (all 43 questions apply) produces false-positive findings because the repo does not hold data, does not expose an API, and does not execute agent-invoked operations.

When `service_archetype` is detected or declared as `stateless-utility` AND at least three of the five surface flags above are `false`, treat the repo as a **dev-library-application** for N/A and scoring purposes: apply the `library` N/A mapping from Step 1 (only ENG-Q1 through ENG-Q5 are non-N/A) as the baseline, then continue with the surface-flag downgrades for the questions that remain.

This override affects scoring only; it does not change the recorded `repo_type`. The original `repo_type` value is preserved in the report metadata, and the override with its rationale is recorded as an INFO note in the report preamble.

### Step 1.6: Service Archetype Detection

If `service_archetype` was provided in `additionalPlanContext`, use that value directly and skip auto-detection. Otherwise, analyze the file inventory from Step 1.3 and the file contents from Step 1.4 to classify the service archetype.

#### Auto-Detection Decision Tree

```
🔍 Analyze Repository
    │
    ▼
┌─────────────────────────────────┐
│ service_archetype in config?     │
│  YES → Use config value          │
│  NO  → Continue ▼                │
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ Has message queue consumers?     │
│ (SQS, Kafka, SNS handlers,      │
│  event bridge rules, no/minimal  │
│  synchronous API surface)        │
│                                  │
│  YES → event-processor           │
│  NO  → Continue ▼                │
└─────────┬───────────────────────┘
          │
          ▼
┌──────────────────────────────────────┐
│ Orchestrates multi-service           │
│ workflows?                           │
│ (Calls 3+ downstream services        │
│  AND coordinates multi-step          │
│  sequences: saga patterns,           │
│  compensating actions, workflow      │
│  state machines, Step Functions,     │
│  or sequential service calls         │
│  with error/rollback handling)       │
│                                      │
│  YES → orchestrator                  │
│  NO  → Continue ▼                    │
└─────────┬────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ Has persistent state?            │
│ (Database connections, Redis     │
│  writes, DynamoDB, SQL, ORM)     │
│                                  │
│  NO  → ▼ (stateless path)       │
│  YES → ▼ (stateful path)        │
└──┬──────────────┬───────────────┘
   │              │
   ▼              ▼
STATELESS       STATEFUL
   │              │
   ▼              ▼
┌──────────┐  ┌──────────────────┐
│ Has write │  │ Primarily read   │
│ endpoints │  │ queries with     │
│ or state  │  │ pagination/      │
│ mutations?│  │ filtering?       │
│           │  │ Minimal business │
│ NO →      │  │ logic?           │
│ stateless │  │                  │
│ -utility  │  │ YES →            │
│           │  │ data-gateway     │
│ YES →     │  │                  │
│ stateful  │  │ NO →             │
│ -crud     │  │ stateful-crud    │
└──────────┘  └──────────────────┘
```

#### Detection Signals by Archetype

**stateless-utility:**
- No database connections, no cache writes, no message queue producers
- All API operations are read-only (GET endpoints, query RPCs)
- Data comes from static files, environment variables, or in-memory computation
- No `user_id`, `session`, or user-specific context in request schemas
- Data is public or reference-grade (exchange rates, product catalogs, configuration)
- Examples: currency converter, feature flag service, configuration service, health check aggregator

**stateful-crud:**
- Database connections (SQL, NoSQL, Redis with writes, DynamoDB)
- Create/Update/Delete endpoints alongside Read
- Entity lifecycle management (status fields, soft deletes)
- User-specific data (user_id in requests, session management)
- Examples: cart service, user profile service, order service, inventory service

**orchestrator:**
- Calls 3+ downstream services (HTTP clients, gRPC stubs, service addresses in env vars)
- Sequential or parallel service call patterns
- Minimal or no persistent state of its own
- Transaction coordination (saga patterns, compensating actions)
- Examples: checkout service, order placement service, workflow coordinator

**data-gateway:**
- Database queries dominate the logic (SQL, Elasticsearch, DynamoDB scans)
- Pagination, filtering, sorting parameters in API
- Search endpoints
- Minimal business logic — primarily data transformation and serialization
- Read-heavy traffic pattern (>80% reads)
- Examples: product search service, reporting API, analytics query service

**event-processor:**
- Message queue consumers (SQS, Kafka, SNS, EventBridge)
- Event handler functions (Lambda triggers, message listeners)
- No synchronous API surface (or minimal — health checks only)
- Batch processing patterns
- May produce events for downstream consumers
- Examples: notification service, ETL pipeline, audit log processor, email sender

#### Archetype Recording

Record the detected archetype in the analysis context. Include it in the report metadata:

```markdown
**Service Archetype**: <archetype> (auto-detected | user-provided)
```

If auto-detection was used, include a brief justification:
```markdown
**Archetype Justification**: <1-2 sentence explanation of why this archetype was selected>
```

## N/A Mapping — Repository Type Question Applicability

Before evaluating any question, check the `repo_type` (resolved in Step 0) against the N/A mapping table below. Questions mapped as N/A for the detected repo type are **not evaluated** — they are recorded directly in the N/A display format and excluded from scoring.

### N/A Question Mappings by Repo Type

| Repo Type | Questions Scored as N/A |
|-----------|------------------------|
| `application` | None — all 43 questions apply |
| `infrastructure-only` | API-Q1 through API-Q8, AUTH-Q4, STATE-Q1 through STATE-Q7, HITL-Q1 through HITL-Q3, DATA-Q1 through DATA-Q7, DISC-Q1 through DISC-Q3 |
| `deployment-config` | All questions N/A **except** ENG-Q1 through ENG-Q5 and AUTH-Q1 through AUTH-Q3 |
| `library` | ENG-Q1 through ENG-Q5 |
| `monorepo` | None — all 43 questions apply (assessed per-service within the repo) |

**Rationale by repo type:**

- **`application`** — Full-stack repositories with source code, APIs, data access, and deployment infrastructure. All 43 questions are relevant because agents will interact with the application's APIs, data, auth, and operational surface. Severity is further calibrated by `service_archetype`.
- **`infrastructure-only`** — Repositories containing only IaC provisioning (Terraform modules, CDK stacks, CloudFormation templates) with no application source code. API, most application-level auth (identity propagation), state management, human-in-the-loop, data accessibility, and discoverability questions do not apply because there is no application runtime to evaluate. Auth questions AUTH-Q1 through AUTH-Q3 and AUTH-Q5 through AUTH-Q7 still apply (machine identity, scoped permissions, action-level auth, credential management, audit logging, agent suspension) because IaC defines IAM roles, policies, and security controls. OBS and ENG questions still apply because infrastructure repos define observability and deployment maturity.
- **`deployment-config`** — Repositories containing only CI/CD pipelines, Kubernetes manifests, Helm charts, GitOps configs, or Ansible playbooks — no application source code. Only engineering maturity (ENG-Q1 through ENG-Q5) and foundational auth (AUTH-Q1 through AUTH-Q3) apply.
- **`library`** — Package repositories with source code but no deployable entry point (no Dockerfile, no IaC, no main()). ENG-Q1 through ENG-Q5 are N/A because libraries have no deployment infrastructure, no CI/CD deployment pipeline, no rollback capability, and no encryption-at-rest configuration. All other questions apply because libraries expose APIs, handle auth, manage state, and process data that agents may consume through dependent applications.
- **`monorepo`** — Repositories containing multiple independent services. All 43 questions apply, assessed per-service within the repo. Each service directory is evaluated independently against the full question set.

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
2. **RISK-SAFETY count** — N/A questions do not count as RISK-SAFETY.
3. **RISK-QUALITY count** — N/A questions do not count as RISK-QUALITY.
4. **INFO count** — N/A questions do not count as INFOs.
5. **Readiness profile determination** — Only non-N/A questions with BLOCKER or RISK-SAFETY severity are used to determine the readiness profile (Agent-Ready, Pilot-Ready, Pilot-Ready (Safety Concerns), Remediation Required, Not Agent-Integrable). N/A questions have no effect on the profile.

### N/A Inclusion Rule

All 43 questions **must appear** in the report output. N/A questions are listed in the detailed findings section using the N/A display format above — they are **not omitted** from the report. Extended questions that were not triggered are listed using the "Not Evaluated" display format:

```markdown
#### <question_id>: <question topic>
- **Severity**: Not Evaluated (extended)
- **Finding**: Extended question not triggered for this service. Archetype: `<archetype>`, agent_scope: `<scope>`.
- **Trigger**: <trigger condition from the extended questions table>
- **Gap**: Not evaluated
- **Recommendation**: Not evaluated
- **Evidence**: Not evaluated
```

This ensures the report is a complete record of all 43 questions regardless of repo type or archetype, and makes it clear which questions were evaluated, skipped (N/A), or not triggered (extended).

### How to Apply the N/A Mapping

For each evaluation step (Steps 2–9), before evaluating a question:

1. Check whether the question ID appears in the N/A mapping for the resolved `repo_type`.
2. If the question **is** in the N/A set: skip evaluation, record the question using the N/A display format, and move to the next question.
3. If the question **is not** in the N/A set: evaluate the question normally against the repository evidence.
4. If **all** questions in a section are N/A for the detected repo type, skip the section evaluation entirely but still list all questions from that section in the report using the N/A display format.


## Question Evaluation — Steps 2–9

Evaluate all 43 questions across the 8 sections (Steps 2–9). The authoritative question bank — every question with its severity, scope-conditional resolution, and surface-flag/archetype calibration — is in **`references/02-question-bank.md`**. Load that file now and evaluate each applicable question against the repository evidence and the resolved `agent_scope`, `repo_type`, surface flags, and service archetype from Steps 0–1.6, honoring the N/A mapping above. Consult **`references/01-scoring-model.md`** for the severity and archetype definitions the question bank references.


## Report Template

After evaluating all 43 questions across Steps 2–9, compile the findings into the four-artifact bundle. The full markdown report structure — metadata header, readiness-profile determination, summary counts, BLOCKERs/RISKs/INFOs, detailed findings for all 43 questions, and evidence index — is in **`references/03-report-template.md`**. Load that file and follow it exactly. The JSON and HTML artifacts render subsets of the same data per the Output Contract.

## Constraints and Guardrails

Strictly follow these rules at all times:

- **Read-only analysis**: Do not modify any source code, configuration, or infrastructure in the repository. Only create the output artifact bundle (md + json + html + metadata.json).
- **Stay on the current branch**: This is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out and perform all work there.
- **Be specific — cite evidence**: Always reference actual file names, resource names, and patterns found. Never write "there may be..." — state what was found or what was not found.
- **Absence is evidence**: If a search for a specific artifact finds nothing (e.g., no OpenAPI spec, no IaC files, no audit logging configuration), that absence is itself a finding. State it clearly and score accordingly.
- **Search completeness for absence claims**: Before declaring an artifact absent, search using ALL detection patterns listed in the question's "Look for" section. At minimum: (1) scan file names matching common conventions (e.g., `openapi.*`, `swagger.*`, `*.tf`, `*.smithy`), (2) grep source files for framework-specific imports or annotations listed in "Look for", (3) check the dependency manifest (package.json, pom.xml, requirements.txt, go.mod) for relevant libraries. If the repo has >500 files, focus on directories most likely to contain the artifact (e.g., `/api`, `/docs`, `/infra`, `/config`, root-level config files). Declare absence only after all detection patterns return zero results. State which patterns were searched in the evidence field.
- **Read before judging**: Do not score a question without actually reading relevant files. If relevant files have not been found yet, keep searching.
- **IaC is ground truth**: Trust IaC definitions over README descriptions. What is deployed is what is defined in the IaC.
- **Do not skip questions**: All 43 questions must appear in the report. Questions that are N/A for the detected `repo_type` use the N/A display format. Extended questions that are not triggered use the "Not Evaluated (extended)" display format. Both are listed, not omitted.
- **N/A scoring rules**: Questions scored as N/A are excluded from BLOCKER, RISK-SAFETY, RISK-QUALITY, and INFO counts and from readiness profile determination.
- **Extended question scoring rules**: Extended questions that are "Not Evaluated" are excluded from all counts and from readiness profile determination — same as N/A. Extended questions that ARE triggered are scored normally (BLOCKER/RISK-SAFETY/RISK-QUALITY/INFO) and count toward the readiness profile.
- **Conditional BLOCKER rules**: The 5 conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2) must be evaluated at the severity determined by `agent_scope`. Do not override the conditional logic.
- **Evaluation tier rules**: Core questions are always evaluated (unless N/A by repo_type). Extended questions are evaluated only when their trigger condition is met. Use the Evaluation Tier tables in the Summary section to determine which extended questions to trigger based on archetype, scope, and service characteristics.
- **Archetype classification**: Use the `service_archetype` from `additionalPlanContext` if provided. Otherwise, auto-detect in Step 1.6. If auto-detection is inconclusive, default to `stateful-crud`. The archetype determines which extended questions are triggered — it does NOT override severity of core questions.
- **Repo type classification**: Use the `repo_type` from `additionalPlanContext`. If not provided, default to `application`. Apply the N/A mapping table exactly as defined.
- **Report completeness**: The output report must contain all required sections: metadata header (including service archetype), readiness profile, summary counts (including extended question counts), BLOCKERs with remediation, RISKs with compensating controls, INFOs, detailed findings for all 43 questions, and evidence index.

## Output Contract

Emit the four-artifact bundle exactly as specified in **`references/04-output-contract.md`**: the unified per-finding field set, the `ara_metadata` subobject, the `evaluations[]` array, classification rules, the four-artifact contract, the HTML visual contract, and error handling. Load that file and conform to it — it is the machine-readable contract the portfolio aggregator and webapp consume.
