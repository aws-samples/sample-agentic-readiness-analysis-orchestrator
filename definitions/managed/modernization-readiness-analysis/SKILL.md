---
name: modernization-readiness-analysis
description: Scans portfolios for cloud-native maturity gaps and maps findings to AWS modernization pathways
type: managed
---

## Name

Modernization Readiness Analysis

## Objective

Evaluate the cloud architecture maturity, operational readiness, and modernization potential of a repository's infrastructure, application architecture, data platforms, security posture, and operational practices. This analysis identifies concrete modernization pathways and produces a scored gap analysis with actionable recommendations. It answers the question: how ready is this system for iterative modernization — whether that means containerizing workloads, decomposing monoliths, migrating to managed services, eliminating license costs, or adopting modern DevOps practices?

## Summary

This transformation performs a dedicated Modernization Readiness Analysis on a codebase. It scans all files in the repository to discover infrastructure-as-code, application source code, CI/CD definitions, API specifications, dependency manifests, configuration files, container definitions, Kubernetes manifests, and Helm charts. It then evaluates what it finds against 37 questions across 5 sections — Infrastructure (INF), Application Architecture (APP), Data Platform (DATA), Security (SEC), and Operations (OPS):

- **INF** — Infrastructure, Platform, and DevOps (11 questions)
- **APP** — Application Architecture (6 questions)
- **DATA** — Data Platform Modernization (4 questions)
- **SEC** — Security Baseline (7 questions)
- **OPS** — Operations & Observability (9 questions)

Each question is scored on a 1–4 scale:

| Score | Label | Meaning |
|-------|-------|---------|
| **4** | ✅ Mature | Fully meets the criterion. No gaps. Best-practice implementation. |
| **3** | 🟡 Partial | Partially meets the criterion. Minor gaps. Functional but improvable. |
| **2** | 🟠 Needs Work | Exists but significant gaps. Moderate effort needed. |
| **1** | ❌ Not Ready | Missing entirely or fundamentally inadequate. |

Category scores are calculated as the arithmetic mean of all non-N/A, non-Not-Evaluated question scores in that category. The overall score is the average of the 5 category scores (each category weighted equally regardless of question count). If all questions in a category are N/A or Not Evaluated for the detected repo_type and archetype, the category score is "N/A" and is excluded from the overall score average.

> **Design note — equal category weighting:** Categories have different question counts (INF: 11, OPS: 9, SEC: 7, APP: 6, DATA: 4). Equal category weighting is intentional: each modernization dimension contributes equally to the overall score regardless of how many questions probe it. This means individual DATA questions have ~2.5x the per-question impact on the overall score compared to individual OPS questions. This is acceptable because data platform modernization (fewer questions, each high-signal) is as important as operational maturity (more questions, individually lower-signal). Portfolio consumers comparing services should use category scores directly rather than relying on overall score alone.

**Not Evaluated (archetype-N/A)** — Questions that are archetype-calibrated (currently INF-Q3, INF-Q4, APP-Q3, APP-Q4) may resolve to "not applicable by design" for a specific archetype. When the archetype column indicates the question does not apply (e.g., "No multi-step workflows exist — not applicable by design" for `stateless-utility` on INF-Q3), record the question as **"Not Evaluated (archetype-N/A)"** and exclude it from both category and overall score averaging — same exclusion as N/A. This prevents artificial score inflation from archetype-correct-but-uninformative "Score 4 by default" entries. The rubric columns still describe what evaluation would look like; the Not-Evaluated status means no evaluation was performed for this repo.

The analysis evaluates 7 AWS Modernization Pathways, each with defined trigger conditions mapped to specific question IDs and contextual guards to prevent false positives. Most pathways use a **Primary + Supporting** trigger model — a pathway fires when its Primary condition is met; Supporting conditions strengthen the case and inform the detail section. Two pathways use **compound triggers** where multiple conditions must be true simultaneously (Move to Cloud Native requires primary AND at least one supporting; Move to Open Source requires primary AND commercial DB evidence). The Summary Table below captures each pathway's full trigger logic — Step 7 is authoritative on implementation details:

| Pathway | Primary Trigger | Supporting Triggers | Contextual Guard |
|---------|----------------|---------------------|------------------|
| **Move to Cloud Native** | APP-Q2 < 3 AND at least one of: INF-Q1 < 3, APP-Q3 < 3, APP-Q4 < 3 | (compound — primary required AND ≥1 supporting required) | — |
| **Move to Containers** | INF-Q1 < 3 AND no container definitions found | — | Must be EC2/VM-based; SHALL NOT trigger if compute is already Lambda/Fargate/ECS |
| **Move to Open Source** | DATA-Q4 < 3 AND commercial DB engines detected in INF-Q2 finding | (compound — both conditions required) | — |
| **Move to Managed Databases** | INF-Q2 < 3 | DATA-Q3 < 3 (strengthens, not required) | — |
| **Move to Managed Analytics** | INF-Q4 < 3 | Data source sprawl with no unified access layer (DATA-Q2 finding) | Evidence of data processing workloads must exist |
| **Move to Modern DevOps** | INF-Q10 < 3 OR INF-Q11 < 3 | OPS-Q5 < 3, OPS-Q6 < 3 (strengthen, not required) | — |
| **Move to AI** | No AI/agent frameworks, no vector DB, no RAG, no agent eval framework | — | Requires AI/agent/LLM intent in portfolio or service context |

Full trigger logic including severity interpretation, archetype calibration, and pathway detail content is defined in Step 7.1 through 7.7. This Summary table is a quick reference — Step 7 is authoritative.

All 7 pathways appear in the pathway summary table with status: **Triggered**, **Not Triggered**, or **Not Applicable** (for repo_types where the pathway does not apply).

When APP-Q2 (Monolith vs Microservices) scores less than 3, the report includes a **Decomposition Strategy** section with concrete approach options (strengthen as modular monolith, Strangler Fig parallel track, conditional/adaptive, and big-bang with recommendation against), pattern recommendations linked to AWS prescriptive guidance (Anti-corruption Layer, Saga, Event Sourcing, Hexagonal Architecture), and level-of-effort estimates per approach.

The output is a **four-artifact bundle** (per the Four-Artifact Output Contract below) containing:
- `{repo-name}-mod-report.md` — richest narrative report
- `{repo-name}-mod-report.json` — canonical machine-readable contract
- `{repo-name}-mod-report.html` — single self-contained HTML visualization
- `{repo-name}-mod-report.metadata.json` — version compatibility sidecar

The MD report contains:
- Metadata header (repo name, date, repo_type)
- Overall and category score table
- Top 5 gaps
- Pathway summary table (all 7 pathways)
- Pathway detail subsections (triggered pathways only)
- Decomposition strategy (conditional on APP-Q2 < 3)
- Detailed findings for all 37 questions (including N/A questions in N/A format)
- Learning materials mapped to triggered pathways
- Evidence index with file references

This analysis targets workloads running on AWS. On-premises and multi-cloud workloads are out of scope unless actively migrating to AWS.

This analysis does NOT cover:
- **Agentic Readiness** — Whether systems can serve as agent tools (API surface quality, agent identity and authorization, transactional integrity, human-in-the-loop controls, agent observability, discoverability). Those concerns use BLOCKER/RISK/INFO severity scoring, readiness profiles, conditional BLOCKERs based on agent_scope, and are covered in the Agentic Readiness Analysis.
- **Agent design** — Prompt engineering, model selection, agent behavioral testing.

## Entry Criteria

- The repository is accessible and readable at the specified path
- The repository contains files relevant to analysis (source code, IaC, API specs, CI/CD configs, dependency manifests, container definitions, Kubernetes manifests, Helm charts, or configuration files)
- Write permissions exist to create the output artifact bundle (MD, JSON, HTML, and metadata.json)
- The analysis operates in **read-only mode** — it will not modify any source code or configuration in the repository
- Stay on the current branch — this is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out.


## Reference Files

This definition is split into a lean orchestration spine (this file) plus four reference files, loaded on demand at the point in the flow where each is needed. Load each file when the step below directs you to — do not skip any.

- **`references/01-question-bank.md`** — the authoritative catalog of all 37 questions (Steps 2–6), each scored 1–4 with its rubric and archetype calibration. Load after Discovery and archetype/surface detection.
- **`references/02-pathways.md`** — the 7 AWS Modernization Pathways with full trigger logic (Step 7), the conditional Decomposition Strategy (Step 8), and the AI/Agent infrastructure evaluation logic (Step 9). Load after scoring the questions.
- **`references/03-report-template.md`** — the markdown report structure: section order, score tables, top-5 gaps, pathway tables, decomposition strategy, detailed findings for all 37 questions, learning materials, evidence index.
- **`references/04-output-contract.md`** — the machine-readable four-artifact contract: unified severity/category display names, per-finding field set, `mod_metadata`, classification rules, per-repo `pathways[]`, and error handling.

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning the discovery scan, read the analysis context from `additionalPlanContext` to determine the repo classification, framing context, and technology preferences that will shape the entire analysis.

#### 0.1 Read Analysis Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `repo_type` | enum | No | `"application"` | Repository classification. One of: `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`. Determines which questions are scored as N/A and which pathways are Not Applicable. |
| `context` | string | No | — | Free-text description of the repository (e.g., "Legacy PHP e-commerce app running on EC2 with MySQL"). Used to frame findings and recommendations throughout the report. |
| `priority` | enum | No | — | Repository priority within the portfolio. One of: `P0`, `P1`, `P2`. Recorded in report metadata. |
| `tags` | string[] | No | — | User-defined tags for categorization (e.g., `["monolith", "php", "payment-critical"]`). Recorded in report metadata. |
| `preferences` | object | No | — | Technology steering preferences with two arrays: `prefer` (technologies to favor in recommendations) and `avoid` (technologies to steer away from). Used to frame technology recommendations throughout the report. |
| `service_archetype` | enum | No | auto-detected | Service archetype for scoring calibration on architecture-sensitive questions. One of: `stateless-utility`, `stateful-crud`, `orchestrator`, `data-gateway`, `event-processor`. If not provided, auto-detected in Step 1.5. Only applies when `repo_type` is `application`. |

**Example `additionalPlanContext`:**

```yaml
additionalPlanContext: |
  repo_type: "application"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  priority: "P0"
  tags: ["monolith", "php", "payment-critical"]
  service_archetype: "stateful-crud"
  preferences:
    prefer: ["eks", "aurora", "graviton"]
    avoid: ["serverless", "dynamodb"]
```

#### 0.2 Apply Defaults

If a field is absent from `additionalPlanContext`, apply these defaults:

- **`repo_type`** → `"application"` — This is the most comprehensive analysis (no questions skipped, all pathways applicable). Defaulting to `application` ensures nothing is missed when classification is unknown.
- **`context`** → No default. If absent, findings and recommendations are written without additional framing.
- **`priority`** → No default. If absent, omitted from report metadata.
- **`tags`** → No default. If absent, omitted from report metadata.
- **`preferences`** → No default. If absent, technology recommendations use neutral language without favoring or avoiding specific technologies.
- **`service_archetype`** → Auto-detected in Step 1.5 based on repository analysis. If auto-detection is inconclusive, defaults to `"stateful-crud"` (the most conservative archetype — applies the strictest rubric on architecture-sensitive questions without false downgrades). Only applies when `repo_type` is `application`. For non-application repo types, this field is ignored.

If `repo_type` is present but not one of the 5 recognized values (`application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`), default to `"application"` and include a warning in the report metadata: **"Unrecognized repo_type '{value}', defaulting to application."**

#### 0.3 Fields NOT Read by This TD

The MOD TD does **not** read, validate, or apply the following fields from `additionalPlanContext`. If present, they are ignored:

- **`agent_scope`** — Not used by this TD. Agent scope governs agent-interaction safety decisions and is not relevant to modernization scoring.

#### 0.4 How Context Fields Are Used

Record the resolved values from Steps 0.1–0.2 in the analysis context. They will be used in subsequent steps as follows:

- **`repo_type`** → Used in the N/A Mapping to determine which questions are scored as N/A and which pathways are marked Not Applicable for the detected repo type. Included in the report metadata header.
- **`context`** → Used throughout the report to frame findings and recommendations with repository-specific context. For example, if context mentions "legacy PHP e-commerce", recommendations reference the specific technology stack and business domain. Also used by the Move to AI pathway (Step 7.7) as a contextual guard. The pathway only triggers when the context explicitly mentions AI/agent/LLM use cases. This prevents false-positive triggers on services where AI adoption is not a goal.
- **`priority`** → Recorded in the report metadata header. Used by the Portfolio MOD TD for service ordering within roadmap phases.
- **`tags`** → Recorded in the report metadata header.
- **`preferences`** → Used throughout the report to steer technology recommendations. When `prefer` contains values, recommendations favor those technologies where applicable (e.g., if `prefer: ["eks"]`, container recommendations reference EKS over ECS). When `avoid` contains values, recommendations steer away from those technologies (e.g., if `avoid: ["serverless"]`, recommendations do not suggest Lambda-based approaches). Preferences influence recommendation framing only — they do not change scores, N/A mappings, or pathway trigger logic.
- **`service_archetype`** → Used in Steps 2–3 to calibrate scoring on architecture-sensitive questions where the "correct" architectural choice depends on the kind of service being evaluated. Specifically, INF-Q3 (Workflow Orchestration), INF-Q4 (Async Messaging and Streaming), APP-Q3 (Async vs Sync Communication), and APP-Q4 (Long-Running Process Handling) use archetype-keyed rubrics so that services whose correct design is synchronous and stateless are not penalized for lacking async infrastructure they do not need. Calibration can both downgrade and upgrade a score relative to the default rubric — for example, a `stateless-utility` using only synchronous HTTP may score 4 on INF-Q4 (correct design), while the same evidence would score 1 for an `orchestrator`. Included in the report metadata header. Only applies when `repo_type` is `application`; for other repo types, archetype calibration is skipped and the default rubric applies.

### Step 1: Discovery — Static Scan

Scan the target repository to build a complete inventory of what exists before evaluating any questions. This discovery step feeds every subsequent evaluation step — questions reference specific file types, patterns, and technology signals identified here.

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

**CI/CD Configurations:**
- GitHub Actions (`.github/workflows/*.yml`)
- GitLab CI (`.gitlab-ci.yml`)
- Jenkins (`Jenkinsfile`)
- AWS CodeBuild (`buildspec.yml`)
- AWS CodeDeploy (`appspec.yml`)
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

**Kubernetes Manifests and Helm Charts:**

This category is particularly important for MOD — Kubernetes and Helm artifacts directly inform infrastructure maturity (INF-Q1), deployment strategy (OPS-Q5), service discovery (APP-Q6), and the Move to Containers pathway.

- Kubernetes manifests (`*.yaml` in `k8s/`, `manifests/`, `deploy/`, `kubernetes/` directories)
- Helm charts (`Chart.yaml`, `values.yaml`, `templates/` directory, `.helmignore`)
- Kustomize overlays (`kustomization.yaml`, `overlays/`, `bases/`)
- ArgoCD application definitions (`Application`, `ApplicationSet` resources)
- Flux CD configurations (`GitRepository`, `HelmRelease`, `Kustomization` resources)
- Service mesh configs (Istio `VirtualService`, `DestinationRule`)
- Kubernetes Operators and CRDs (Custom Resource Definitions)

**Database Configurations:**

Database artifacts inform Data Platform questions (DATA-Q1–Q4), Managed Databases pathway, and Open Source pathway triggers.

- Database engine definitions in IaC (`aws_rds_instance`, `aws_dynamodb_table`, `aws_docdb_cluster`, `aws_elasticache_*`)
- Database connection strings and driver configurations in source code and config files
- SQL migration files (`.sql` files, Flyway `V*.sql`, Liquibase `*.xml`/`*.yaml`)
- Stored procedures, triggers, and functions (`CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION`)
- ORM configurations (Hibernate, SQLAlchemy, Prisma, TypeORM, Entity Framework)
- Database engine version pins in IaC or Helm values

**Analytics and Streaming Infrastructure:**

Analytics artifacts inform the Move to Managed Analytics pathway and INF-Q4 (async messaging/streaming).

- Streaming infrastructure in IaC (`aws_kinesis_*`, `aws_msk_*`, Kafka configs)
- Data pipeline definitions (Step Functions, Airflow DAGs, Glue jobs)
- Data lake configurations (S3 bucket policies, Lake Formation, Athena queries)
- ETL/ELT scripts and configurations
- Self-managed Kafka or RabbitMQ in Docker Compose or Kubernetes manifests

**AI/Agent Frameworks:**

AI artifacts inform the Move to AI pathway trigger.

- AI/ML framework imports in source code (Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, SageMaker SDK)
- Vector database infrastructure (OpenSearch with vector engine, Pinecone, pgvector, Weaviate, Qdrant)
- RAG implementation patterns (embedding generation, vector store queries, retrieval chains)
- Agent evaluation frameworks (Ragas, DeepEval, custom eval harnesses)
- Model configuration files (Bedrock model IDs, endpoint configs, prompt templates)

**Configuration Files:**
- Application config (`*.yaml`, `*.yml`, `*.json`, `*.toml`, `*.properties`, `*.ini`)
- Environment files (`.env`, `.env.*`)
- Service mesh configs
- Feature flag configurations

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
- `.helm/` — Helm cache directories
- `charts/` — Downloaded Helm chart dependencies (when inside a chart's dependency cache, not user-authored charts)

#### 1.3 Build the File Inventory

After scanning, compile a structured inventory of what was found. This inventory is referenced throughout Steps 2–6 when evaluating individual questions. Record:

- **IaC files found** — Terraform, CloudFormation, CDK, Helm, Kustomize, and other IaC files with paths. Used by: INF-Q1 (managed compute), INF-Q2 (managed databases), INF-Q5 (network security), INF-Q7 (auto-scaling), INF-Q8 (backup/recovery), INF-Q9 (high availability), INF-Q10 (IaC coverage), SEC-Q1 (audit logging), SEC-Q2 (encryption at rest).
- **Source code files found** — Application source files by language. Used by: APP-Q1 (languages), APP-Q2 (monolith vs microservices), APP-Q3 (async vs sync), APP-Q4 (long-running processes), DATA-Q2 (data access layer), DATA-Q4 (stored procedures).
- **API spec files found** — OpenAPI, AsyncAPI, and GraphQL files. Used by: APP-Q5 (API versioning), APP-Q6 (service discovery).
- **CI/CD config files found** — Pipeline definitions. Used by: INF-Q11 (CI/CD automation), OPS-Q5 (deployment strategy), OPS-Q6 (integration testing), SEC-Q7 (security pipeline).
- **Container and Kubernetes files found** — Dockerfiles, compose files, Kubernetes manifests, Helm charts. Used by: INF-Q1 (managed compute), APP-Q2 (microservices detection), APP-Q6 (service discovery), OPS-Q5 (deployment strategy), Move to Containers pathway.
- **Dependency manifests found** — Package manifests by ecosystem. Used by: APP-Q1 (language detection), identifying frameworks and libraries across multiple questions.
- **Database artifacts found** — Database definitions in IaC, migration files, stored procedures, ORM configs, engine versions. Used by: INF-Q2 (managed databases), DATA-Q1–Q4, Move to Open Source pathway, Move to Managed Databases pathway.
- **Analytics and streaming artifacts found** — Streaming infrastructure, data pipelines, ETL configs. Used by: INF-Q4 (async messaging/streaming), Move to Managed Analytics pathway.
- **AI/agent artifacts found** — AI framework imports, vector DB configs, RAG patterns, eval frameworks. Used by: Move to AI pathway trigger.
- **Configuration files found** — Config files by type. Used by: SEC-Q5 (secrets management), OPS-Q9 (resource tagging).
- **Notable absences** — Record what was NOT found. Absence is evidence: if no IaC files exist, that informs INF-Q10. If no CI/CD configs exist, that informs INF-Q11. If no container files exist, that informs the Move to Containers pathway. If no AI/agent artifacts exist, that informs the Move to AI pathway. These absences are cited in evaluation steps.

#### 1.4 Read Discovered Files

Read all discovered files that are relevant to the analysis. Prioritize reading in this order:

1. **IaC files** — Reveal infrastructure architecture, compute model, database choices, network topology, and security configuration
2. **Kubernetes manifests and Helm charts** — Reveal container orchestration maturity, service mesh usage, deployment strategies, and scaling configuration
3. **CI/CD configuration files** — Reveal deployment automation, testing practices, and security scanning
4. **Dependency manifests** — Reveal technology stack, frameworks, AI/ML libraries, and database drivers
5. **Database artifacts** — Reveal database engine choices, version pins, stored procedure usage, and migration patterns
6. **Container definitions** — Reveal containerization state and runtime configuration
7. **Application source code** — Reveal architecture patterns (monolith vs microservices), communication patterns (sync vs async), data access patterns, and AI/agent framework usage
8. **Configuration files** — Reveal runtime settings, secrets management, and tagging practices

For large repositories, focus on files most relevant to the 37 evaluation questions. Not every source file needs to be read in full — prioritize IaC resources, Kubernetes manifests, database configurations, pipeline definitions, entry points, and inter-service communication patterns.

### Step 1.5: Service Archetype Detection

Service archetype classifies an application by its **runtime architectural role**, which determines what the "correct" design looks like for communication patterns, persistence, and orchestration. Architecture-sensitive questions in this TD (INF-Q3, INF-Q4, APP-Q3, APP-Q4) score the same evidence differently depending on archetype — synchronous HTTP is correct for a stateless utility and an anti-pattern for an orchestrator.

**This archetype model is owned by the MOD TD and is applied to MOD scoring only.** It is independent of any other transformation definition. If `service_archetype` was provided in `additionalPlanContext`, use that value directly and skip auto-detection. Otherwise, analyze the file inventory from Step 1.3 and the file contents from Step 1.4 to classify the archetype using the decision logic below.

Archetype detection applies only when `repo_type` is `application`. For `infrastructure-only`, `deployment-config`, and `library`, skip this step — there is no application runtime to classify. For `monorepo`, detect archetype per service.

#### Archetypes and Their Detection Signals

| Archetype | Description | Detection Signals |
|-----------|-------------|-------------------|
| **stateless-utility** | Pure-function services with no persistent state, no user-specific data, and no write operations. Correct design is synchronous request/response. | No database connections, no cache writes, no message queue producers. All API operations are read-only (GET endpoints, query RPCs). Data comes from static files, environment variables, or in-memory computation. No `user_id`, `session`, or user-specific context. Data is public or reference-grade. Examples: currency converter, feature flag reader, config service, health aggregator. |
| **stateful-crud** | Services that own persistent state and expose CRUD operations on business entities. | Database connections (SQL, NoSQL, Redis with writes, DynamoDB). Create/Update/Delete endpoints alongside Read. Entity lifecycle management (status fields, soft deletes). User-specific data (user_id, session). Examples: cart service, user profile service, order service, inventory service. |
| **orchestrator** | Services that coordinate multi-service workflows by calling other services. Correct design leans async with managed orchestration. | High fan-out — calls 3+ downstream services (HTTP clients, gRPC stubs, service addresses in env vars). Sequential or parallel service-call patterns. Minimal or no persistent state of its own. Transaction coordination (saga patterns, compensating actions). Examples: checkout service, order placement service, workflow coordinator. |
| **data-gateway** | Read-heavy data access layer — APIs over databases, search indexes, or data lakes. Synchronous reads are the primary and correct pattern. | Database queries dominate the logic (SQL, Elasticsearch, DynamoDB scans). Pagination, filtering, sorting parameters in API. Search endpoints. Minimal business logic — primarily data transformation and serialization. Read-heavy traffic (>80% reads). Examples: product search service, reporting API, analytics query service. |
| **event-processor** | Services that consume events/messages and process them asynchronously. Correct design has no or minimal synchronous API surface. | Message queue consumers (SQS, Kafka, SNS, EventBridge). Event handler functions (Lambda triggers, message listeners). No synchronous API surface, or minimal (health checks only). Batch processing patterns. Examples: notification service, ETL pipeline, audit log processor, email sender. |

#### Auto-Detection Decision Logic

Apply these checks in order. The first check that matches determines the archetype.

1. **Has message queue consumers with no (or minimal) synchronous API surface?** → `event-processor`
   - SQS/Kafka/SNS handlers, EventBridge rules, Lambda triggers on queue events
   - No HTTP routes, or only health-check routes

2. **Orchestrates multi-service workflows (calls 3+ downstream services AND coordinates multi-step sequences)?** → `orchestrator`
   - HTTP/gRPC clients to 3+ other services with sequential/conditional coordination logic
   - Saga patterns, compensating actions, or workflow state machines
   - Step Functions, Temporal, or equivalent orchestration frameworks
   - Important: simple fan-out (calling 3 services independently without coordination) is NOT sufficient — the service must coordinate a workflow. A CRUD service calling auth + DB + notifications independently is `stateful-crud`, not `orchestrator`.

3. **Has persistent state?** → go to 3a
   **No persistent state?** → go to 3b

   **3a. Has write endpoints or state mutations?**
   - **Yes** → `stateful-crud`
   - **No, primarily read queries with pagination/filtering and minimal business logic** → `data-gateway`

   **3b. Stateless, has write endpoints or state mutations?**
   - **No** → `stateless-utility`
   - **Yes** (writes but no owned persistent state — e.g., forwarder to another service) → `stateful-crud` (treat as conservative default)

4. **If the above signals are ambiguous or conflicting**, default to `stateful-crud`. This is the conservative choice — it applies the strictest rubric on architecture-sensitive questions without false downgrades, matching the behavior of the default (non-calibrated) rubric.

#### Archetype Recording

Record the detected archetype in the analysis context. Include it in the report metadata header:

```markdown
**Service Archetype**: <archetype> (auto-detected | user-provided)
```

If auto-detection was used, include a one- to two-sentence justification referencing the specific signals observed:

```markdown
**Archetype Justification**: <e.g., "No database connections or writes detected; all endpoints are GET operations reading from a static JSON file. Classified as stateless-utility.">
```

If archetype detection is skipped because `repo_type` is not `application`, omit these fields from the metadata header.

### Step 1.6: Target-System Surface Detection

Some MOD questions evaluate a system's maturity on a specific operational surface — a persistent data store, an at-rest-encryption surface, a multi-AZ surface. For repositories that **do not expose that surface at all** (e.g., a progress-bar library has no database, a build tool has no data at rest, a pure utility has no multi-AZ decision to make), scoring those questions with Score 1 ("no managed database" / "no encryption at rest") produces false positives and crowds out the genuine findings on repositories that *do* expose the surface.

This step records six surface flags that feed surface-gated calibration on a small number of INF, SEC, and OPS questions. Surface flags are derived from the Step 1 file inventory — no additional scanning is needed.

#### Flags

| Flag | True when |
|------|-----------|
| `has_persistent_data_store` | IaC defines a database resource (`aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*`, `aws_neptune_*`, `aws_timestreamwrite_*`, `aws_elasticache_*`), a self-managed database is declared in Docker Compose / Kubernetes manifests / Helm charts, or the source code imports a database driver (JDBC, SQLAlchemy, Mongoose, go-sql-driver, `pymongo`, `redis`, etc.) paired with connection/pool configuration. Libraries that provide a database *adapter* without themselves deploying a store are `false`. |
| `has_at_rest_data_surface` | Any of the following exists in IaC or detected at runtime: S3 buckets, RDS/Aurora/DynamoDB/DocumentDB/Neptune/Timestream/ElastiCache, EBS volumes attached to workloads, EFS file systems, managed block/object storage. `has_persistent_data_store=true` implies `has_at_rest_data_surface=true`. Source-code-only repositories with no deployment artifacts are `false`. |
| `has_deployed_workload` | IaC defines deployable compute (`aws_ecs_*`, `aws_eks_*`, `aws_lambda_*`, `aws_instance`, `aws_apprunner_*`, EKS/ECS task definitions, Lambda functions) OR a Dockerfile exists AND deployment manifests (Helm chart, Kubernetes manifests, CloudFormation / Terraform) reference it. Pure library repos (no Dockerfile, no IaC, published via NpmPrettyMuch/PyPI/Maven Central) are `false`. |
| `has_api_surface` | The codebase defines HTTP/gRPC/RPC endpoints (Express/FastAPI/Flask/Spring MVC/gRPC server bindings, API Gateway resources in IaC, ALB listeners, AppSync schemas). CLI tools, SDK libraries, and pure computation utilities are `false`. |
| `has_multi_instance_deployment` | The deployment model supports more than one running instance — ASG with desired>1, Kubernetes Deployment with replicas>1, ECS service with desired_count>1, Lambda (inherently multi-instance), serverless. Single-EC2 or single-container deployments are `false`. Used for INF-Q9 multi-AZ calibration. |
| `has_iac_provisioning_aws_resources` | The repository contains IaC (Terraform, CDK, CloudFormation, Pulumi, SAM) that provisions AWS resources — any `aws_*` Terraform resources, CloudFormation `AWS::*` resource types, CDK constructs that synthesize AWS resources, or SAM templates. Repositories with only Dockerfiles, Kubernetes manifests, Helm charts, or CI/CD pipeline definitions (without AWS resource provisioning) are `false`. Libraries and application repos with no IaC are `false`. This flag distinguishes repos that *own* AWS infrastructure from repos that are *deployed onto* infrastructure managed elsewhere. **Foundation vs Application IaC:** This flag is `true` for both foundation IaC (CloudTrail, AWS Config, VPC baselines, Organization SCPs) and application IaC (ECS tasks, RDS instances, Lambda functions). The SEC-Q1 gate additionally checks for account-level scope — see the SEC-Q1 gate row for details. |

#### Surface-flag gates on scoring

Questions marked with a surface gate below evaluate to **"Not Evaluated (archetype-N/A)"** when the required flag is `false`, rather than defaulting to Score 1.

| Question | Gate flag required | Behavior when flag is `false` |
|----------|-------------------|-------------------------------|
| **INF-Q2** (Managed Databases) | `has_persistent_data_store` | Not Evaluated (archetype-N/A). Finding: "This system does not deploy a database. INF-Q2 does not apply." |
| **SEC-Q2** (Encryption at Rest) | `has_at_rest_data_surface` | Not Evaluated (archetype-N/A). Finding: "This system has no deployed data-at-rest surface — no database, S3 bucket, EBS volume, or similar. SEC-Q2 does not apply." |
| **INF-Q8** (Backup/Recovery) | `has_persistent_data_store` OR `has_at_rest_data_surface` | Not Evaluated (archetype-N/A). Finding: "This system has no persistent state to back up. INF-Q8 does not apply." |
| **INF-Q9** (High Availability) | `has_deployed_workload` AND (`has_api_surface` OR `has_persistent_data_store`) | Not Evaluated (archetype-N/A). Finding: "This system has no deployed workload requiring HA evaluation. INF-Q9 does not apply." |
| **OPS-Q2** (SLOs) | `has_api_surface` OR `has_persistent_data_store` | Not Evaluated (archetype-N/A). Finding: "This system has no user-facing surface for which SLOs are meaningful. OPS-Q2 does not apply." |
| **SEC-Q1** (Audit Logging) | `has_iac_provisioning_aws_resources` AND evidence of account-level IaC scope | Not Evaluated (archetype-N/A). Finding: "Audit logging (CloudTrail) is an AWS account-level service provisioned once per account or organization — not per-application. This repo contains application-level IaC only (compute, databases, networking for this service) which is the correct scope for an application repo. CloudTrail evaluation belongs in the foundation/account-level infrastructure repo. Future: provide audit logging status via `additionalPlanContext`." |
| **OPS-Q5** (Deployment Strategy) | `has_deployed_workload` | Not Evaluated (archetype-N/A). Finding: "No deployed workload found in this repo — deployment strategy cannot be assessed from source code alone. Deployment orchestration may exist in a separate deployment-config or GitOps repo. Future: provide deployment strategy evidence via `additionalPlanContext`." |

When a flag is `true`, the question is evaluated normally against its rubric — surface flags never downgrade a real Score 1, they only prevent a false Score 1 on a system that does not expose the surface at all. Record the resolved surface flags in the report metadata:

**SEC-Q1 Account-Level Scope Determination:**

The SEC-Q1 gate requires both `has_iac_provisioning_aws_resources=true` AND evidence that the IaC operates at account/foundation level (not just application level). Evaluate SEC-Q1 only when the repo's IaC includes **account-level resources** such as:

- `aws_cloudtrail`, `aws_config_*`, `aws_guardduty_*`, `aws_securityhub_*`
- `aws_organizations_*`, `aws_iam_account_*`, Service Control Policies
- Account-wide VPC baselines, Transit Gateway, shared networking
- Centralized logging infrastructure (log archive buckets, log aggregation)

**Do NOT evaluate SEC-Q1** when the repo contains only application-level IaC:
- ECS/EKS/Lambda definitions for this service
- RDS/DynamoDB/S3 for this service's data
- Security groups, ALBs, API Gateways for this service
- Service-specific IAM roles and policies

**Rationale:** CloudTrail is provisioned once per AWS account or organization. An application repo that defines its own ECS service and RDS database is correctly scoped — it should not also define CloudTrail. Penalizing application IaC repos for lacking account-level resources produces false positives. Only repos whose explicit purpose is account/foundation infrastructure should be evaluated on SEC-Q1.

```markdown
**Surface Flags**: has_persistent_data_store=<true|false>, has_at_rest_data_surface=<true|false>, has_deployed_workload=<true|false>, has_api_surface=<true|false>, has_multi_instance_deployment=<true|false>, has_iac_provisioning_aws_resources=<true|false>
```

Surface flags apply to all `repo_type` values where the flag is meaningful. Libraries (`library` repo_type) already receive Not-Evaluated treatment for most INF questions via the N/A mapping; surface flags tighten the same pattern for `application` and `monorepo` repos that happen to lack specific surfaces.

## N/A Mapping — Repository Type Question and Pathway Applicability

Before evaluating any question or pathway, check the `repo_type` (resolved in Step 0) against the N/A mapping tables below. Questions and pathways mapped as N/A for the detected repo type are **not evaluated** — they are recorded directly in the N/A display format and excluded from scoring.

The MOD N/A Mapping has two dimensions:

1. **Question N/A Mappings** — Which of the 37 questions are scored as N/A per repo_type
2. **Pathway N/A Mappings** — Which of the 7 AWS Modernization Pathways are marked Not Applicable per repo_type

### N/A Question Mappings by Repo Type

| Repo Type | Questions Scored as N/A |
|-----------|------------------------|
| `application` | None — all 37 questions apply |
| `infrastructure-only` | APP-Q1 through APP-Q6, DATA-Q1 through DATA-Q2, DATA-Q4 |
| `deployment-config` | APP-Q1 through APP-Q6, DATA-Q1 through DATA-Q4, INF-Q1 through INF-Q4, INF-Q6 through INF-Q9 |
| `library` | INF-Q1 through INF-Q11, OPS-Q2 through OPS-Q9 |
| `monorepo` | None — all 37 questions apply (assessed per-service within the repo) |

**Rationale by repo type:**

- **`application`** — Full-stack repositories with source code, infrastructure, and deployment configuration. All 37 questions are relevant because the analysis evaluates the complete modernization surface: infrastructure maturity, application architecture, data platform, security baseline, and operational practices.
- **`infrastructure-only`** — Repositories containing only IaC provisioning (Terraform modules, CDK stacks, CloudFormation templates) with no application source code. Application Architecture questions (APP-Q1 through APP-Q6) do not apply because there is no application runtime to evaluate for language choice, monolith decomposition, communication patterns, or service discovery. Data questions DATA-Q1 (unstructured data storage) and DATA-Q2 (unified data access layer) do not apply because there is no application data access layer. DATA-Q4 (stored procedures) does not apply because there is no application-layer business logic to evaluate for database coupling. DATA-Q3 (database engine version) still applies because IaC defines database resources with engine versions. All INF, SEC, and OPS questions still apply because infrastructure repos define compute, networking, security, and operational configuration.
- **`deployment-config`** — Repositories containing only CI/CD pipelines, Kubernetes manifests, Helm charts, GitOps configs, or Ansible playbooks — no application source code. Application Architecture questions (APP-Q1 through APP-Q6) do not apply because there is no application to evaluate. All Data Platform questions (DATA-Q1 through DATA-Q4) do not apply because deployment config repos do not define data storage or access patterns. Infrastructure questions INF-Q1 through INF-Q4 (managed compute, managed databases, workflow orchestration, async messaging) do not apply because deployment config repos do not provision these resources — they configure how existing resources are deployed. INF-Q6 through INF-Q9 (API entry point, auto-scaling, backup/recovery, high availability) do not apply for the same reason. INF-Q5 (network security) still applies because deployment manifests may define network policies, security groups, or service mesh rules. INF-Q10 (IaC coverage) and INF-Q11 (CI/CD automation) still apply because they evaluate the deployment config repo's own governance. All SEC and OPS questions still apply because deployment repos define security scanning, secrets management, deployment strategies, and observability configuration.
- **`library`** — Package repositories with source code but no deployable entry point (no Dockerfile, no IaC, no main()). All INF questions (INF-Q1 through INF-Q11) are N/A because libraries have no infrastructure to provision, no compute to manage, no databases to configure, no networking to secure, no auto-scaling to tune, and no CI/CD deployment pipeline (they have build/publish pipelines, not deployment pipelines). OPS-Q2 through OPS-Q9 are N/A because libraries do not define SLOs, publish business metrics, configure anomaly detection, implement deployment strategies, run integration tests against live services, automate incident response, own observability dashboards, or manage resource tagging. OPS-Q1 (distributed tracing) still applies because libraries can instrument tracing that propagates through dependent applications. All APP, DATA, and SEC questions still apply because libraries contain application code, data access patterns, and security practices that affect consuming applications.
- **`monorepo`** — Repositories containing multiple independent services. All 37 questions apply, assessed per-service within the repo. Each service directory is evaluated independently against the full question set.

### N/A Pathway Mappings by Repo Type

| Repo Type | Pathways Marked as Not Applicable |
|-----------|-----------------------------------|
| `application` | None — all 7 pathways applicable |
| `infrastructure-only` | Move to Cloud Native, Move to Containers, Move to AI, Move to Managed Analytics |
| `deployment-config` | Move to Cloud Native, Move to Containers, Move to Open Source, Move to Managed Databases, Move to Managed Analytics, Move to AI (all except Move to Modern DevOps) |
| `library` | Move to Containers, Move to Modern DevOps, Move to Managed Databases, Move to Managed Analytics, Move to Cloud Native |
| `monorepo` | None — all 7 pathways applicable |

**Rationale by repo type:**

- **`application`** — All 7 pathways are potentially relevant for full-stack application repositories.
- **`infrastructure-only`** — Move to Cloud Native, Move to Containers, and Move to AI do not apply because there is no application to decompose, containerize, or add AI capabilities to. Move to Managed Analytics does not apply because infrastructure repos do not run data processing workloads. Move to Open Source, Move to Managed Databases, and Move to Modern DevOps still apply because IaC repos define database engines (which may be commercial), database management mode (self-managed vs managed), and deployment automation practices.
- **`deployment-config`** — Only Move to Modern DevOps applies because deployment config repos are fundamentally about DevOps practices (CI/CD, deployment strategies, IaC governance). All other pathways require application source code, database definitions, or compute infrastructure that deployment config repos do not contain.
- **`library`** — Move to Containers does not apply because libraries are not deployed as running services. Move to Modern DevOps does not apply because libraries use build/publish pipelines, not deployment pipelines. Move to Managed Databases and Move to Managed Analytics do not apply because libraries do not provision or manage database or analytics infrastructure. Move to Cloud Native does not apply because libraries are not independently deployable units. Move to Open Source and Move to AI still apply because libraries may contain commercial database drivers or lack AI capabilities that could enhance their functionality.
- **`monorepo`** — All 7 pathways are potentially relevant, evaluated per-service within the repo.

### N/A Display Format

When a question is N/A for the detected `repo_type`, record it as:

| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `{repo_type}` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |

Replace `{repo_type}` with the actual resolved repo type value (e.g., "This is a `infrastructure-only` repository. This question does not apply.").

### Not Evaluated (archetype-N/A) Display Format

When an archetype-calibrated question (INF-Q3, INF-Q4, APP-Q3, APP-Q4) resolves to "not applicable by design" for the detected archetype, record it as:

| Field | Value |
|-------|-------|
| **Score** | Not Evaluated (archetype-N/A) |
| **Finding** | This service is a `{archetype}`. {Question topic} is not applicable by design — {brief reason, e.g., "no multi-step workflows exist for a stateless utility"}. |
| **Gap** | N/A |
| **Recommendation** | N/A |

Not-Evaluated questions are **excluded from category and overall score averaging** — treated identically to N/A for scoring purposes.

When a pathway is N/A for the detected `repo_type`, record it in the pathway summary table as:

| Field | Value |
|-------|-------|
| **Status** | Not Applicable |
| **Reason** | This is a `{repo_type}` repository. This pathway does not apply. |

### N/A and Not-Evaluated Scoring Rules

N/A questions and Not-Evaluated (archetype-N/A) questions are **both excluded from the numerator and denominator** of category score averages:

1. **Category score calculation** — The category score is the arithmetic mean of only the non-N/A, non-Not-Evaluated question scores in that category. Both are excluded from the sum of scores (numerator) and the count of questions (denominator). For example, if a category has 6 questions, 1 is N/A for repo_type, and 1 is Not Evaluated (archetype-N/A), the category score = (sum of 4 remaining scores) / 4.
2. **All-exclusion category** — If **all** questions in a category are N/A or Not Evaluated, the category score is **"N/A"** and that category is excluded from the overall score average.
3. **Overall score calculation** — The overall score is the average of the non-N/A category scores. Each non-N/A category is weighted equally regardless of question count.
4. **Pathway exclusion** — N/A pathways are listed in the pathway summary table with status "Not Applicable" but do not affect the count of triggered vs not-triggered pathways.

> **Why Not-Evaluated matters:** A `stateless-utility` that correctly has no workflows (INF-Q3) should not score 4 "by design" — that inflates its infrastructure category above a `stateful-crud` with appropriate Step Functions coverage (realistic Score 3). Recording as Not Evaluated (archetype-N/A) keeps scores comparable across archetypes.

### N/A Inclusion Rule

All 37 questions **must appear** in the report output. N/A questions are listed in the detailed findings section using the N/A display format above — they are **not omitted** from the report. This ensures the report is a complete record of all 37 questions regardless of repo type, and makes it clear which questions were skipped and why.

All 7 pathways **must appear** in the pathway summary table. N/A pathways are listed with status "Not Applicable" — they are **not omitted** from the table.

### How to Apply the N/A Mapping

For each evaluation step (Steps 2–6), before evaluating a question:

1. Check whether the question ID appears in the N/A question mapping for the resolved `repo_type`.
2. If the question **is** in the N/A set: skip evaluation, record the question using the N/A display format, and move to the next question.
3. If the question **is not** in the N/A set: evaluate the question normally against the repository evidence.
4. If **all** questions in a section are N/A for the detected repo type, skip the section evaluation entirely but still list all questions from that section in the report using the N/A display format. Record the category score as "N/A".

For pathway evaluation:

1. Check whether the pathway appears in the N/A pathway mapping for the resolved `repo_type`.
2. If the pathway **is** in the N/A set: record it in the pathway summary table with status "Not Applicable" and the N/A reason. Do not evaluate trigger conditions.
3. If the pathway **is not** in the N/A set: evaluate the pathway's trigger conditions and contextual guards normally against the question scores and discovery evidence.



## Question Evaluation — Steps 2–6

Score all 37 questions (1–4) across the 5 sections (Steps 2–6). The authoritative question bank — every question with its rubric and archetype calibration — is in **`references/01-question-bank.md`**. Load that file now and score each applicable question against the repository evidence and the resolved `repo_type`, service archetype, and surface flags from Steps 0–1.6, honoring the N/A mapping and surface-gate rules above.


## Modernization Pathways — Steps 7–9

After scoring the questions, evaluate the 7 AWS Modernization Pathways, the conditional Decomposition Strategy, and the AI/Agent infrastructure logic. The full trigger logic and contextual guards are in **`references/02-pathways.md`** (Step 7 is authoritative over the Summary quick-reference table). Load that file and follow it.


## Report Template

After evaluating questions and pathways, compile the findings into the four-artifact bundle. The full markdown report structure — section order, score tables, top-5 gaps, pathway tables, decomposition strategy, detailed findings for all 37 questions, learning materials, and evidence index — is in **`references/03-report-template.md`**. Load that file and follow it exactly. The JSON and HTML artifacts render subsets of the same data per the Output Contract.

## Constraints and Guardrails

The following constraints govern the analysis execution and report generation. These are non-negotiable rules that the evaluating agent MUST follow.

### C1: Read-Only Analysis

This analysis operates in **read-only mode**. The evaluating agent SHALL NOT:
- Modify any source code, configuration files, or infrastructure definitions in the repository.
- Create, delete, or rename any files in the repository (except the output artifact bundle).
- Execute any commands that change repository state (no `git commit`, no `terraform apply`, no `npm install`).
- Create, switch, or checkout any git branches. Remain on whatever branch is currently checked out. This is an analysis-only task — do not create branches for runs.

The only write operations permitted are creating the output artifact bundle: `{repo-name}-mod-report.md`, `{repo-name}-mod-report.json`, `{repo-name}-mod-report.html`, and `{repo-name}-mod-report.metadata.json`.

### C2: All 37 Questions Must Appear in Report

Every one of the 37 questions MUST appear in the Detailed Findings section of the report, regardless of repo_type. Questions that are N/A for the detected repo_type are listed using the N/A display format — they are never omitted. This ensures the report is a complete record of all 37 evaluation criteria.

### C3: All 7 Pathways Must Appear in Pathway Table

Every one of the 7 AWS Modernization Pathways MUST appear in the Pathway Summary Table, regardless of status. Pathways that are Not Triggered or Not Applicable are listed with their respective status and reason — they are never omitted from the table.

### C4: Evidence-Based Findings

Every finding MUST cite specific evidence from the repository:
- **File paths** — Reference the specific files that support the finding (e.g., `terraform/main.tf`, `src/app/server.ts`, `.github/workflows/deploy.yml`).
- **Resource names** — Reference specific IaC resource names, service names, or configuration keys.
- **Absence is evidence** — If a search for specific artifacts finds nothing, that absence is itself a finding. State what was searched for and that it was not found (e.g., "No Dockerfile or container definitions found in the repository"), and name the searched path in the finding's `evidence.file` — an absence finding with `evidence: null` is an unsupported finding.

Do not make findings based on assumptions or general knowledge. Every score must be traceable to specific repository evidence or documented absence of evidence.

### C5: Honest Calibration

Scores MUST reflect genuine analysis of the repository evidence:
- **A score of 4 means genuinely mature** — the criterion is fully met with no gaps and best-practice implementation. Do not award a 4 for partial compliance or "good enough."
- **A score of 3 means partial** — the criterion is mostly met with minor gaps. This is the appropriate score when the capability exists but has room for improvement.
- **A score of 2 means needs work** — the capability exists but has significant gaps requiring moderate effort to address.
- **A score of 1 means not present** — the capability is missing entirely or fundamentally inadequate.

Avoid score inflation. A repository with basic infrastructure and no automation should not score above 2.0 overall. A repository with comprehensive, well-architected infrastructure should score 3.5+. The scores should meaningfully differentiate between mature and immature systems.

### C6: Preference Framing Only

When `preferences` (prefer/avoid arrays) are provided in additionalPlanContext:
- Preferences influence **recommendation framing only** — they steer which technologies are suggested in recommendations and pathway details.
- Preferences do NOT change scores, N/A mappings, pathway trigger logic, or any evaluation criteria.
- If `prefer: ["eks"]`, container recommendations should reference EKS over ECS where applicable.
- If `avoid: ["serverless"]`, recommendations should not suggest Lambda-based approaches.
- If no preferences are provided, recommendations use neutral technology language without favoring or avoiding specific technologies.

### C7: Ignored Fields

The following fields from `additionalPlanContext` are not used by this TD and are ignored if present: `goal`, `goal_context`, `agent_scope`.

---

## Output Contract

Emit the four-artifact bundle exactly as specified in **`references/04-output-contract.md`**: the unified severity/category display names, the unified per-finding field set, the `mod_metadata` subobject, classification rules and the consistency check, per-repo `pathways[]` emission, the four-artifact contract, and error handling. Load that file and conform to it — it is the machine-readable contract the portfolio aggregator and webapp consume.
