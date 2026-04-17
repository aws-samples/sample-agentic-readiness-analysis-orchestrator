## Name

Modernization Readiness Assessment

## Objective

Evaluate the cloud architecture maturity, operational readiness, and modernization potential of a repository's infrastructure, application architecture, data platforms, security posture, and operational practices. This assessment identifies concrete modernization pathways and produces a scored gap analysis with actionable recommendations. It answers the question: how ready is this system for iterative modernization — whether that means containerizing workloads, decomposing monoliths, migrating to managed services, eliminating license costs, or adopting modern DevOps practices?

## Summary

This transformation performs a dedicated Modernization Readiness Assessment on a codebase. It scans all files in the repository to discover infrastructure-as-code, application source code, CI/CD definitions, API specifications, dependency manifests, configuration files, container definitions, Kubernetes manifests, and Helm charts. It then evaluates what it finds against 37 questions across 5 sections:

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
| **1** | ❌ Not Present | Missing entirely or fundamentally inadequate. |

Category scores are calculated as the arithmetic mean of all non-N/A question scores in that category. The overall score is the average of the 5 category scores (each category weighted equally regardless of question count). If all questions in a category are N/A for the detected repo_type, the category score is "N/A" and is excluded from the overall score average.

The assessment evaluates 7 AWS Modernization Pathways, each with defined trigger conditions mapped to specific question IDs and contextual guards to prevent false positives:

| Pathway | Primary Triggers | Contextual Guard |
|---------|-----------------|------------------|
| **Move to Cloud Native** | APP-Q2 < 3, INF-Q1 < 3, APP-Q3 < 3, APP-Q4 < 3 | — |
| **Move to Containers** | INF-Q1 < 3, no container definitions found | Must be EC2/VM-based; SHALL NOT trigger if compute is already Lambda/Fargate/ECS |
| **Move to Open Source** | DATA-Q4 < 3, commercial DB engines detected | — |
| **Move to Managed Databases** | INF-Q2 < 3, DATA-Q3 < 3 | — |
| **Move to Managed Analytics** | INF-Q4 < 3, data source sprawl with no unified access layer | Evidence of data processing workloads must exist |
| **Move to Modern DevOps** | INF-Q10 < 3, INF-Q11 < 3, OPS-Q5 < 3, OPS-Q6 < 3 | — |
| **Move to AI** | No AI/agent frameworks, no vector DB, no RAG, no agent eval framework | Requires AI/agent/LLM intent in portfolio or service context |

All 7 pathways appear in the pathway summary table with status: **Triggered**, **Not Triggered**, or **Not Applicable** (for repo_types where the pathway does not apply).

When APP-Q2 (Monolith vs Microservices) scores less than 3, the report includes a **Decomposition Strategy** section with concrete approach options (Strangler Fig parallel track, conditional/adaptive, and big-bang with recommendation against), pattern recommendations linked to AWS prescriptive guidance (Anti-corruption Layer, Saga, Event Sourcing, Hexagonal Architecture), and level-of-effort estimates per approach.

A **Quick Agent Wins** section identifies agent opportunities based on assessment findings — only where the system has sufficient foundation to support them (e.g., API docs exist, CI/CD pipeline exists, structured logging in place).

The output is a structured Markdown report saved as `{repo-name}-mod-report.md` containing:
- Metadata header (repo name, date, repo_type)
- Overall and category score table
- Top 5 gaps
- Quick Agent Wins
- Pathway summary table (all 7 pathways)
- Pathway detail subsections (triggered pathways only)
- Decomposition strategy (conditional on APP-Q2 < 3)
- Detailed findings for all 37 questions (including N/A questions in N/A format)
- Learning materials mapped to triggered pathways
- Evidence index with file references

This assessment does NOT cover:
- **Agentic Readiness** — Whether systems can serve as agent tools (API surface quality, agent identity and authorization, transactional integrity, human-in-the-loop controls, agent observability, discoverability). Those concerns use BLOCKER/RISK/INFO severity scoring, readiness profiles, conditional BLOCKERs based on agent_scope, and are covered in the Agentic Readiness Assessment.
- **Agent design** — Prompt engineering, model selection, agent behavioral testing.

## Entry Criteria

- The repository is accessible and readable at the specified path
- The repository contains files relevant to assessment (source code, IaC, API specs, CI/CD configs, dependency manifests, container definitions, Kubernetes manifests, Helm charts, or configuration files)
- Write permissions exist to create the output report file
- The assessment operates in **read-only mode** — it will not modify any source code or configuration in the repository

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning the discovery scan, read the assessment context from `additionalPlanContext` to determine the repo classification, framing context, and technology preferences that will shape the entire assessment.

#### 0.1 Read Assessment Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `repo_type` | enum | No | `"application"` | Repository classification. One of: `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`. Determines which questions are scored as N/A and which pathways are Not Applicable. |
| `context` | string | No | — | Free-text description of the repository (e.g., "Legacy PHP e-commerce app running on EC2 with MySQL"). Used to frame findings and recommendations throughout the report. |
| `priority` | enum | No | — | Repository priority within the portfolio. One of: `P0`, `P1`, `P2`. Recorded in report metadata. |
| `tags` | string[] | No | — | User-defined tags for categorization (e.g., `["monolith", "php", "payment-critical"]`). Recorded in report metadata. |
| `preferences` | object | No | — | Technology steering preferences with two arrays: `prefer` (technologies to favor in recommendations) and `avoid` (technologies to steer away from). Used to frame technology recommendations throughout the report. |

**Example `additionalPlanContext`:**

```yaml
additionalPlanContext: |
  repo_type: "application"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  priority: "P0"
  tags: ["monolith", "php", "payment-critical"]
  preferences:
    prefer: ["eks", "aurora", "graviton"]
    avoid: ["serverless", "dynamodb"]
```

#### 0.2 Apply Defaults

If a field is absent from `additionalPlanContext`, apply these defaults:

- **`repo_type`** → `"application"` — This is the most comprehensive assessment (no questions skipped, all pathways applicable). Defaulting to `application` ensures nothing is missed when classification is unknown.
- **`context`** → No default. If absent, findings and recommendations are written without additional framing.
- **`priority`** → No default. If absent, omitted from report metadata.
- **`tags`** → No default. If absent, omitted from report metadata.
- **`preferences`** → No default. If absent, technology recommendations use neutral language without favoring or avoiding specific technologies.

If `repo_type` is present but not one of the 5 recognized values (`application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`), default to `"application"` and include a warning in the report metadata: **"Unrecognized repo_type '{value}', defaulting to application."**

#### 0.3 Fields NOT Read by This TD

The MOD TD does **not** read, validate, or apply the following fields from `additionalPlanContext`. If present, they are ignored:

- **`agent_scope`** — Not used by this TD. Agent scope is an ARA-only concept.

#### 0.4 How Context Fields Are Used

Record the resolved values from Steps 0.1–0.2 in the assessment context. They will be used in subsequent steps as follows:

- **`repo_type`** → Used in the N/A Mapping to determine which questions are scored as N/A and which pathways are marked Not Applicable for the detected repo type. Included in the report metadata header.
- **`context`** → Used throughout the report to frame findings and recommendations with repository-specific context. For example, if context mentions "legacy PHP e-commerce", recommendations reference the specific technology stack and business domain. Also used by the Move to AI pathway (Step 7.7) as a contextual guard. The pathway only triggers when the context explicitly mentions AI/agent/LLM use cases. This prevents false-positive triggers on services where AI adoption is not a goal.
- **`priority`** → Recorded in the report metadata header. Used by the Portfolio MOD TD for service ordering within roadmap phases.
- **`tags`** → Recorded in the report metadata header.
- **`preferences`** → Used throughout the report to steer technology recommendations. When `prefer` contains values, recommendations favor those technologies where applicable (e.g., if `prefer: ["eks"]`, container recommendations reference EKS over ECS). When `avoid` contains values, recommendations steer away from those technologies (e.g., if `avoid: ["serverless"]`, recommendations do not suggest Lambda-based approaches). Preferences influence recommendation framing only — they do not change scores, N/A mappings, or pathway trigger logic.

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
- Service mesh configs (Istio `VirtualService`, `DestinationRule`; App Mesh `VirtualNode`, `VirtualRouter`)
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

AI artifacts inform the Move to AI pathway trigger and the Quick Agent Wins section.

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
- `.helm/` — Helm cache directories
- `charts/` — Downloaded Helm chart dependencies (when inside a chart's dependency cache, not user-authored charts)

#### 1.3 Build the File Inventory

After scanning, compile a structured inventory of what was found. This inventory is referenced throughout Steps 2–6 when evaluating individual questions. Record:

- **IaC files found** — Terraform, CloudFormation, CDK, Helm, Kustomize, and other IaC files with paths. Used by: INF-Q1 (managed compute), INF-Q2 (managed databases), INF-Q5 (network security), INF-Q7 (auto-scaling), INF-Q8 (backup/recovery), INF-Q9 (high availability), INF-Q10 (IaC coverage), SEC-Q1 (audit logging), SEC-Q2 (encryption at rest).
- **Source code files found** — Application source files by language. Used by: APP-Q1 (languages), APP-Q2 (monolith vs microservices), APP-Q3 (async vs sync), APP-Q4 (long-running processes), DATA-Q2 (data access layer), DATA-Q4 (stored procedures).
- **API spec files found** — OpenAPI, AsyncAPI, and GraphQL files. Used by: APP-Q5 (API versioning), APP-Q6 (service discovery), Quick Agent Wins.
- **CI/CD config files found** — Pipeline definitions. Used by: INF-Q11 (CI/CD automation), OPS-Q5 (deployment strategy), OPS-Q6 (integration testing), SEC-Q7 (security pipeline).
- **Container and Kubernetes files found** — Dockerfiles, compose files, Kubernetes manifests, Helm charts. Used by: INF-Q1 (managed compute), APP-Q2 (microservices detection), APP-Q6 (service discovery), OPS-Q5 (deployment strategy), Move to Containers pathway.
- **Dependency manifests found** — Package manifests by ecosystem. Used by: APP-Q1 (language detection), identifying frameworks and libraries across multiple questions.
- **Database artifacts found** — Database definitions in IaC, migration files, stored procedures, ORM configs, engine versions. Used by: INF-Q2 (managed databases), DATA-Q1–Q4, Move to Open Source pathway, Move to Managed Databases pathway.
- **Analytics and streaming artifacts found** — Streaming infrastructure, data pipelines, ETL configs. Used by: INF-Q4 (async messaging/streaming), Move to Managed Analytics pathway.
- **AI/agent artifacts found** — AI framework imports, vector DB configs, RAG patterns, eval frameworks. Used by: Move to AI pathway trigger, Quick Agent Wins.
- **Configuration files found** — Config files by type. Used by: SEC-Q5 (secrets management), OPS-Q9 (resource tagging).
- **Notable absences** — Record what was NOT found. Absence is evidence: if no IaC files exist, that informs INF-Q10. If no CI/CD configs exist, that informs INF-Q11. If no container files exist, that informs the Move to Containers pathway. If no AI/agent artifacts exist, that informs the Move to AI pathway. These absences are cited in evaluation steps.

#### 1.4 Read Discovered Files

Read all discovered files that are relevant to the assessment. Prioritize reading in this order:

1. **IaC files** — Reveal infrastructure architecture, compute model, database choices, network topology, and security configuration
2. **Kubernetes manifests and Helm charts** — Reveal container orchestration maturity, service mesh usage, deployment strategies, and scaling configuration
3. **CI/CD configuration files** — Reveal deployment automation, testing practices, and security scanning
4. **Dependency manifests** — Reveal technology stack, frameworks, AI/ML libraries, and database drivers
5. **Database artifacts** — Reveal database engine choices, version pins, stored procedure usage, and migration patterns
6. **Container definitions** — Reveal containerization state and runtime configuration
7. **Application source code** — Reveal architecture patterns (monolith vs microservices), communication patterns (sync vs async), data access patterns, and AI/agent framework usage
8. **Configuration files** — Reveal runtime settings, secrets management, and tagging practices

For large repositories, focus on files most relevant to the 37 evaluation questions. Not every source file needs to be read in full — prioritize IaC resources, Kubernetes manifests, database configurations, pipeline definitions, entry points, and inter-service communication patterns.

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

- **`application`** — Full-stack repositories with source code, infrastructure, and deployment configuration. All 37 questions are relevant because the assessment evaluates the complete modernization surface: infrastructure maturity, application architecture, data platform, security baseline, and operational practices.
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

When a pathway is N/A for the detected `repo_type`, record it in the pathway summary table as:

| Field | Value |
|-------|-------|
| **Status** | Not Applicable |
| **Reason** | This is a `{repo_type}` repository. This pathway does not apply. |

### N/A Scoring Rules

N/A questions are **excluded from both the numerator and denominator** of category score averages:

1. **Category score calculation** — The category score is the arithmetic mean of only the non-N/A question scores in that category. N/A questions are excluded from both the sum of scores (numerator) and the count of questions (denominator). For example, if a category has 6 questions and 2 are N/A, the category score = (sum of 4 non-N/A scores) / 4.
2. **All-N/A category** — If **all** questions in a category are N/A for the detected repo_type, the category score is **"N/A"** and that category is excluded from the overall score average. For example, if the Application Architecture category (APP-Q1 through APP-Q6) is entirely N/A for an `infrastructure-only` repo, the overall score is calculated from the remaining 4 categories instead of 5.
3. **Overall score calculation** — The overall score is the average of the non-N/A category scores. Each non-N/A category is weighted equally regardless of question count.
4. **Pathway exclusion** — N/A pathways are listed in the pathway summary table with status "Not Applicable" but do not affect the count of triggered vs not-triggered pathways.

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


### Step 2: Infrastructure, Platform, and DevOps (INF-Q1 through INF-Q11)

These questions evaluate the compute, networking, platform services, and deployment practices underpinning the application. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### INF-Q1: Managed Compute

**Question:** What percentage of compute workloads use managed container orchestration (EKS, ECS, Fargate) or serverless (Lambda) vs raw EC2?

**Why it matters:** Managed compute provides elastic scaling, reduced operational overhead, and faster deployment cycles. EC2 requires manual scaling, patching, and capacity planning. Modernization starts with moving off self-managed compute.

| Score | Criteria |
|-------|----------|
| **4** | 80%+ of compute is ECS/EKS/Lambda/Fargate. EC2 only for edge cases. |
| **3** | Mix of managed and EC2, with managed compute for primary workloads. |
| **2** | Primarily EC2 with some containerization or Lambda for auxiliary functions. |
| **1** | All compute on raw EC2 or on-premises with no managed services. |

> **Look for:** Terraform `aws_ecs_*`, `aws_eks_*`, `aws_lambda_*` vs `aws_instance`; CloudFormation resource types; Dockerfile presence; Kubernetes manifests.

#### INF-Q2: Managed Databases

**Question:** Are databases fully managed (RDS/Aurora/DynamoDB/DocumentDB) vs self-managed?

**Why it matters:** Self-managed databases — regardless of where they run (EC2, containers, on-premises) — introduce maintenance windows, manual patching, and operational overhead. Migrating to managed services eliminates ops burden and enables automatic backups, failover, and scaling. This is a primary target for AWS DMS/SCT-based migration pathways.

| Score | Criteria |
|-------|----------|
| **4** | All databases are managed services with automated failover. |
| **3** | Primary databases managed; some auxiliary self-managed instances remain. |
| **2** | Mix of managed and self-managed, or managed but single-AZ without failover. |
| **1** | All databases self-managed on EC2, containers, or on-premises. |

> **Look for:** Terraform `aws_rds_*`, `aws_dynamodb_*`, `aws_docdb_*` vs compute resources running database software; connection strings pointing to self-hosted instances; database engine installation in Dockerfiles or user-data scripts.

#### INF-Q3: Workflow Orchestration

**Question:** Are workflow orchestration services used (Step Functions, Temporal, Camunda) or are workflows primarily implemented as hardcoded application logic?

**Why it matters:** Dedicated workflow orchestration provides visual workflow management, error handling, retry logic, and state management. Without it, all orchestration logic is buried in code — harder to maintain, debug, and evolve.

| Score | Criteria |
|-------|----------|
| **4** | Dedicated workflow orchestration service in use for business-critical workflows. |
| **3** | Partial adoption — some workflows orchestrated, others still in code. |
| **2** | Simple state machines in code with some structure, but no dedicated service. |
| **1** | No orchestration — all workflow logic hardcoded in application code. |

> **Look for:** `aws_sfn_*` in Terraform; Temporal SDK imports; workflow YAML definitions; state machine patterns in code.

#### INF-Q4: Async Messaging and Streaming

**Question:** Is there managed messaging or streaming infrastructure (SQS, SNS, EventBridge, MSK, Kinesis) vs self-managed Kafka/RabbitMQ, or no messaging at all?

**Why it matters:** Managed messaging and streaming enable event-driven architectures with reduced operational overhead. Self-managed message brokers and streaming platforms require patching, scaling, and monitoring. Async patterns are foundational for decoupled, resilient architectures.

| Score | Criteria |
|-------|----------|
| **4** | Managed messaging and/or streaming services in use for inter-service communication and data pipelines. |
| **3** | Managed messaging for some flows; synchronous HTTP or self-managed components for others. |
| **2** | Self-managed messaging/streaming (Kafka, RabbitMQ on EC2/containers). |
| **1** | No messaging or streaming infrastructure — all communication is synchronous HTTP, batch-only data pipelines. |

> **Look for:** `aws_sqs_*`, `aws_sns_*`, `aws_msk_*`, `aws_kinesis_*` in IaC; SDK imports for messaging/streaming; event-driven patterns in code; stream consumer patterns.

#### INF-Q5: Network Security

**Question:** Are services deployed in a VPC with private subnets, security groups, NACLs, and proper network segmentation?

**Why it matters:** Network segmentation limits blast radius of failures and security incidents. Services exposed directly to the internet without proper network controls are a security and operational risk.

| Score | Criteria |
|-------|----------|
| **4** | Services in private subnets, least-privilege security groups, network segmentation present. |
| **3** | VPC with subnets but some overly permissive rules or missing segmentation. |
| **2** | Basic VPC setup but services in public subnets or with 0.0.0.0/0 rules. |
| **1** | No VPC configuration or services deployed outside VPC controls. |

> **Look for:** `aws_vpc`, `aws_subnet`, `aws_security_group`; subnet tiers (public vs private); security group rules; overly permissive rules (0.0.0.0/0).

#### INF-Q6: API Entry Point

**Question:** Is there an API Gateway, ALB, or CloudFront as the entry point vs direct service exposure?

**Why it matters:** A managed entry point provides throttling, authentication, request validation, and a single point of control. Direct service exposure lacks these protections and makes it harder to manage traffic patterns.

| Score | Criteria |
|-------|----------|
| **4** | API Gateway with throttling, auth, and request validation. |
| **3** | ALB or CloudFront with basic routing and health checks. |
| **2** | Load balancer present but minimal configuration (no auth, no throttling). |
| **1** | Services exposed directly with no gateway or load balancer. |

> **Look for:** `aws_api_gateway_*`, `aws_apigatewayv2_*`, `aws_lb_*` in IaC; throttling and auth config on gateway.

#### INF-Q7: Auto-Scaling

**Question:** Are auto-scaling mechanisms configured for compute workloads?

**Why it matters:** Without auto-scaling, workloads cannot respond to traffic spikes or scale down during low demand. This leads to either over-provisioning (cost waste) or under-provisioning (degraded experience).

| Score | Criteria |
|-------|----------|
| **4** | All compute tiers have auto-scaling configured with appropriate min/max. |
| **3** | Auto-scaling on primary compute; some static capacity for auxiliary services. |
| **2** | Basic auto-scaling with default settings, not tuned for workload patterns. |
| **1** | No auto-scaling — all capacity is statically provisioned. |

> **Look for:** `aws_autoscaling_*`, `aws_appautoscaling_*`; scaling policies; min/max capacity settings; Lambda concurrency limits.

#### INF-Q8: Backup and Recovery

**Question:** Are automated backups configured for data stores with defined retention periods and tested restore procedures?

**Why it matters:** Without automated backups and tested restores, a data loss event can wipe application state and cause cascading failures. This is a foundational reliability requirement. (WAF: REL 9)

| Score | Criteria |
|-------|----------|
| **4** | All production data stores have automated backups with defined retention; PITR enabled where supported; restore procedures documented or tested. |
| **3** | Automated backups configured but missing PITR or missing on some data stores; no documented restore testing. |
| **2** | Backups on primary database only; no backup plans for other data stores; no restore testing. |
| **1** | No backup configuration found; or backup_retention_period = 0. |

> **Look for:** `backup_retention_period` on RDS; `point_in_time_recovery` on DynamoDB; `aws_backup_plan` resources; S3 versioning; EBS snapshot lifecycle policies.

#### INF-Q9: High Availability and Fault Isolation

**Question:** Are production workloads deployed across multiple Availability Zones with fault isolation?

**Why it matters:** Single-AZ production deployments are one of the most common high-risk issues. An AZ failure takes down the entire workload with no automatic recovery. Multi-AZ ensures survivability without human intervention. (WAF: REL 10, REL 11)

| Score | Criteria |
|-------|----------|
| **4** | All production compute and data stores span 2+ AZs; load balancers with cross-zone enabled. |
| **3** | Primary database is Multi-AZ but some compute or caches are single-AZ. |
| **2** | Database is single-AZ; compute spans multiple AZs but no explicit fault isolation. |
| **1** | All resources in a single AZ; or no AZ configuration found. |

> **Look for:** `multi_az = true` on RDS; `availability_zones` spanning 2+ AZs in ASGs/ECS; subnet configurations across multiple AZs.

#### INF-Q10: Infrastructure as Code Coverage

**Question:** What percentage of infrastructure is defined in IaC vs manually created?

**Why it matters:** Low IaC coverage means infrastructure changes are manual, error-prone, and non-reproducible. IaC is the foundation for automated deployments, environment consistency, and disaster recovery.

| Score | Criteria |
|-------|----------|
| **4** | 90%+ of infrastructure defined in IaC (compute, networking, databases, messaging). |
| **3** | 70-90% IaC coverage — primary resources covered, some auxiliary resources manual. |
| **2** | Partial IaC — some resources defined, but significant manual infrastructure. |
| **1** | No IaC — all infrastructure created manually (ClickOps). |

> **Look for:** Presence and coverage of .tf files, CDK stacks, CloudFormation templates, Helm charts. Check whether IaC covers compute, networking, databases, and messaging.

#### INF-Q11: CI/CD Automation

**Question:** Are CI/CD pipelines automated with build, test, and deploy stages, or are deployments manual?

**Why it matters:** Manual deployments create bottlenecks, are error-prone, and prevent rapid iteration. Automated pipelines enable continuous delivery with consistent quality gates.

| Score | Criteria |
|-------|----------|
| **4** | Full CI/CD automation with test, build, and deploy stages including automated rollback. |
| **3** | CI/CD pipeline exists with build and deploy, but limited automated testing. |
| **2** | Partial automation — build is automated but deployment is manual or semi-manual. |
| **1** | No CI/CD — all deployments are manual scripts or ClickOps. |

> **Look for:** .github/workflows/, buildspec.yml, Jenkinsfile, CodePipeline definitions in IaC; pipeline stages with automated test, build, and deploy steps.


### Step 3: Application Architecture (APP-Q1 through APP-Q6)

These questions evaluate the application's structural maturity, decomposition readiness, and communication patterns. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### APP-Q1: Programming Languages

**Question:** What programming languages are used and how mature is their ecosystem for cloud-native development?

**Why it matters:** Language choice affects framework availability, community support, hiring, and modernization options. Some languages have richer ecosystems for containers, serverless, and cloud-native patterns.

| Score | Criteria |
|-------|----------|
| **4** | Python, TypeScript/JavaScript, Go, or Java/Kotlin — mature cloud-native ecosystems. |
| **3** | .NET, Ruby, or Rust — solid ecosystems with some gaps. |
| **2** | PHP, Perl, or older Java versions (< 11) — functional but limited modern tooling. |
| **1** | COBOL, VB6, Classic ASP, or legacy languages with minimal cloud-native support. |

> **Look for:** File extensions; package.json, requirements.txt, pom.xml/build.gradle, go.mod, *.csproj.

#### APP-Q2: Monolith vs Microservices

**Question:** Is the application a single deployable unit or multiple independently deployable services?

**Why it matters:** Monoliths limit independent scaling, deployment, and team autonomy. Understanding the current decomposition state and coupling level determines the modernization strategy — containerize as-is, strangler fig extraction, or full decomposition.

| Score | Criteria |
|-------|----------|
| **4** | Microservices or modular monolith with well-defined module boundaries, no circular dependencies, clear interfaces. |
| **3** | Modular monolith with some coupling, or early-stage microservices with shared databases. |
| **2** | Monolith with identifiable modules but significant coupling (shared state, database coupling, circular dependencies). |
| **1** | Tightly-coupled monolith with no clear module boundaries, pervasive shared state. |

> **Look for:** Single deployable vs multiple service directories; Helm charts for multiple services; Docker Compose with multiple services; IaC for multiple ECS tasks or Lambda functions. For monoliths: package/module structure, dependency graphs, circular dependencies, shared mutable state, database coupling.

#### APP-Q3: Async vs Sync Communication

**Question:** What percentage of inter-service communication is asynchronous vs synchronous HTTP?

**Why it matters:** Synchronous-only architectures create tight coupling, cascading failures, and timeout risks. Async patterns enable decoupling, resilience, and better handling of variable-latency operations.

| Score | Criteria |
|-------|----------|
| **4** | 50%+ async, or async available for all long-running operations. |
| **3** | Mix of async and sync with async for key workflows. |
| **2** | Primarily synchronous with some async for background jobs. |
| **1** | All communication is synchronous HTTP with no async patterns. |

> **Look for:** HTTP client calls (axios, requests, RestTemplate, fetch) vs message publishing patterns; event-driven handlers; queue consumers.

#### APP-Q4: Long-Running Process Handling

**Question:** Are operations over 30 seconds handled asynchronously with status polling or callbacks?

**Why it matters:** Blocking calls for long-running operations create timeout risks, poor user experience, and resource waste. Async patterns with status tracking enable better resource utilization and user feedback.

| Score | Criteria |
|-------|----------|
| **4** | All operations over 30 seconds implemented as async jobs with status polling or callbacks. |
| **3** | Most long-running operations are async; some blocking calls remain. |
| **2** | Some background job processing but inconsistent patterns. |
| **1** | All operations are synchronous regardless of duration. |

> **Look for:** Background job frameworks (Celery, Bull, SQS workers); async/polling patterns; job status APIs; Lambda async invocations; Step Functions for long processes.

#### APP-Q5: API Versioning Strategy

**Question:** Is there a consistent API versioning strategy (URL paths, headers, query parameters)?

**Why it matters:** Without versioning, API changes break all consumers simultaneously. Versioning enables graceful migration and backward compatibility.

| Score | Criteria |
|-------|----------|
| **4** | Consistent versioning strategy with backward compatibility guarantees. |
| **3** | Versioning present but inconsistent across endpoints. |
| **2** | Ad hoc versioning — some endpoints versioned, others not. |
| **1** | No versioning — breaking changes deployed directly. |

> **Look for:** /v1/, /v2/ URL patterns; Accept-Version headers; versioning annotations; changelog files.

#### APP-Q6: Service Discovery

**Question:** Is there a service registry, API catalog, or service mesh for service-to-service communication?

**Why it matters:** Hard-coded service endpoints create deployment coupling and make it difficult to scale, relocate, or replace services. Service discovery enables dynamic routing and decoupled deployments.

| Score | Criteria |
|-------|----------|
| **4** | Service discovery mechanism present; no hard-coded service endpoints. |
| **3** | Partial service discovery — some services use discovery, others use hard-coded endpoints. |
| **2** | Environment variables for endpoints but no dynamic discovery. |
| **1** | All service endpoints hard-coded in application code or configuration. |

> **Look for:** AWS Service Discovery, App Mesh, Istio, Consul; API Gateway as catalog; environment variables with hard-coded endpoints vs service discovery.


### Step 4: Data Platform Modernization (DATA-Q1 through DATA-Q4)

These questions evaluate the data layer's modernization state — managed services, schema health, and migration readiness. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### DATA-Q1: Unstructured Data Storage

**Question:** Are documents and unstructured data stored in managed object storage (S3) with parsing capabilities (Textract, Tika)?

**Why it matters:** Unstructured data locked in file systems, local storage, or legacy document management systems is inaccessible for modern workloads. S3 with parsing pipelines enables search, analytics, and AI integration.

| Score | Criteria |
|-------|----------|
| **4** | Unstructured data stored in S3 with parsing pipeline available. |
| **3** | Data in S3 but no automated parsing or extraction pipeline. |
| **2** | Data in managed storage but not S3 (EFS, EBS volumes) with limited accessibility. |
| **1** | Data on local file systems, legacy document management, or inaccessible storage. |

> **Look for:** `aws_s3_bucket`; Textract calls; document parsing libraries; PDF/image processing.

#### DATA-Q2: Unified Data Access Layer

**Question:** Is there a unified data access layer vs scattered database connections throughout the code?

**Why it matters:** Scattered data access means multiple integration points, inconsistent query patterns, and difficulty enforcing data contracts. A unified layer provides a single point of control for data access.

| Score | Criteria |
|-------|----------|
| **4** | Unified data access layer; single point of data contract. |
| **3** | Mostly centralized with some direct access in auxiliary code paths. |
| **2** | Repository/DAO pattern in some modules but inconsistent across the codebase. |
| **1** | Database imports and queries scattered across many modules with no pattern. |

> **Look for:** Centralized repository/DAO layer vs database imports spread across many modules; data access pattern consistency.

#### DATA-Q3: Database Engine Version and EOL

**Question:** Does IaC or deployment configuration specify the database engine version, and have any engines approaching or past end-of-life (EOL) been identified?

**Why it matters:** EOL database engines introduce security vulnerabilities and lack modern features. Unversioned or implicitly-latest configurations are also a risk signal. Engine version awareness is a prerequisite for migration planning.

| Score | Criteria |
|-------|----------|
| **4** | All database engine versions explicitly pinned in IaC; no engines at or past EOL. |
| **3** | Versions pinned but some approaching EOL within 12 months. |
| **2** | Some versions pinned, others implicit; EOL status unknown. |
| **1** | No version pinning; engines at or past EOL detected. |

> **Look for:** Engine version parameters in `aws_rds_instance`, `aws_docdb_cluster`, `aws_elasticache_*`; engine version strings in docker-compose or Helm values; absence of explicit version pinning.

#### DATA-Q4: Stored Procedures and Schema Complexity

**Question:** Does the application rely on stored procedures, triggers, or proprietary SQL constructs (e.g., T-SQL, PL/SQL)?

**Why it matters:** Stored procedures and proprietary SQL tightly couple business logic to the database engine, creating migration blockers. High stored procedure usage signals that database modernization will require significant effort beyond a lift-and-shift — logic extraction and schema refactoring become prerequisites.

| Score | Criteria |
|-------|----------|
| **4** | No stored procedures or proprietary SQL; all business logic in application layer. |
| **3** | Minimal stored procedures for performance-critical operations only. |
| **2** | Moderate stored procedure usage with some proprietary SQL constructs. |
| **1** | Heavy reliance on stored procedures, triggers, and proprietary SQL across the application. |

> **Look for:** `.sql` files containing `CREATE PROCEDURE`, `CREATE TRIGGER`, `CREATE FUNCTION`; ORM bypass patterns (raw SQL execution); references to proprietary SQL dialects in migration files.


### Step 5: Security Baseline (SEC-Q1 through SEC-Q7)

These questions evaluate the foundational security posture required for any modernization initiative. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### SEC-Q1: Audit Logging

**Question:** Is CloudTrail enabled with immutable logs?

**Why it matters:** Audit logging is a compliance and operational requirement for any production system. Immutable logs ensure that actions can be traced and forensic analysis is possible after incidents.

| Score | Criteria |
|-------|----------|
| **4** | CloudTrail enabled with log file validation and immutable storage (S3 Object Lock). |
| **3** | CloudTrail enabled but without immutable storage or log validation. |
| **2** | Partial logging — some services logged, others not. |
| **1** | No CloudTrail or equivalent audit logging. |

> **Look for:** `aws_cloudtrail` in IaC; CloudTrail log file validation enabled; S3 bucket with object lock for logs; CloudWatch log retention policies.

#### SEC-Q2: Encryption at Rest

**Question:** Is KMS used for sensitive data at rest?

**Why it matters:** Encryption at rest is a baseline security requirement. Customer-managed KMS keys provide control over key rotation, access policies, and audit trails.

| Score | Criteria |
|-------|----------|
| **4** | Customer-managed KMS keys for all sensitive data stores. |
| **3** | AWS-managed encryption enabled on most data stores. |
| **2** | Encryption enabled on some data stores but not all. |
| **1** | No encryption at rest configured. |

> **Look for:** `kms_key_id` on S3/RDS/DynamoDB/EBS; `aws_kms_key` resources; encryption config on data stores.

#### SEC-Q3: API Authentication

**Question:** Is there per-request authentication with OAuth2/JWT on all API endpoints?

**Why it matters:** Unauthenticated APIs are a security vulnerability. Per-request authentication ensures that every call is authorized and attributable.

| Score | Criteria |
|-------|----------|
| **4** | Every API endpoint authenticated; OAuth2/JWT standard in use. |
| **3** | Most endpoints authenticated; some internal endpoints lack auth. |
| **2** | Basic authentication (API keys) without token-based auth. |
| **1** | No API authentication — endpoints are open. |

> **Look for:** Auth middleware; API Gateway authorizers; Cognito user pools; OAuth2 flows; Bearer token validation; @Authenticated annotations.

#### SEC-Q4: Centralized Identity Integration

**Question:** Does the application integrate with a centralized identity provider (Cognito, Okta, Ping), or does it manage its own authentication independently?

**Why it matters:** Applications with their own auth systems create inconsistency and increase attack surface. Detecting whether the app integrates with a centralized IdP signals modernization maturity. Apps with standalone auth are harder to integrate into unified access policies.

| Score | Criteria |
|-------|----------|
| **4** | Application integrates with centralized IdP; SSO enabled. |
| **3** | Application uses centralized IdP for most flows; some legacy auth paths remain. |
| **2** | Application has its own auth but can federate with external IdPs. |
| **1** | Application manages its own authentication entirely with no external IdP integration. |

> **Look for:** `aws_cognito_*`; OIDC/SAML configuration; identity provider federation; SSO configuration.

#### SEC-Q5: Secrets Management

**Question:** Are secrets (database credentials, API keys, tokens) managed through a dedicated secrets management system (AWS Secrets Manager, HashiCorp Vault) with rotation, or are they hardcoded in code, environment variables, or configuration files?

**Why it matters:** Hardcoded secrets are a critical security vulnerability and a common finding in legacy applications. Secrets management with rotation and audit trails is a baseline security requirement for any production system, not just agentic workloads.

| Score | Criteria |
|-------|----------|
| **4** | All secrets in Secrets Manager or Vault with automated rotation; no hardcoded credentials. |
| **3** | Most secrets managed; some legacy environment variables remain. |
| **2** | Mix of managed and hardcoded secrets; no rotation. |
| **1** | Secrets hardcoded in code or committed to version control. |

> **Look for:** `aws_secretsmanager_*` in IaC; Vault client imports; hardcoded patterns (password=, secret=, api_key= in code); .env files committed to git.

#### SEC-Q6: Compute Hardening and Patching

**Question:** Are compute resources hardened with managed patching and vulnerability scanning?

**Why it matters:** Unpatched compute resources are high-value targets. Managed patching and vulnerability scanning are baseline security requirements. (WAF: SEC 6)

| Score | Criteria |
|-------|----------|
| **4** | SSM Patch Manager or equivalent configured; vulnerability scanning (Inspector/Snyk) enabled; hardened base images. |
| **3** | Some patching automation but not comprehensive; or vulnerability scanning present but not integrated into CI/CD. |
| **2** | Manual patching process; default AMIs with no hardening. |
| **1** | No evidence of patching strategy; no vulnerability scanning. |

> **Look for:** SSM Agent in user-data; `aws_ssm_patch_baseline`; AWS Inspector or Snyk; hardened AMI references (CIS, Bottlerocket); EC2 Image Builder pipelines.

#### SEC-Q7: Application Security Pipeline

**Question:** Are SAST, DAST, or dependency vulnerability scanning tools integrated into the CI/CD pipeline?

**Why it matters:** Without automated security scanning, vulnerabilities in dependencies or application code reach production undetected. Embedding security validation in the pipeline is a baseline practice. (WAF: SEC 11)

| Score | Criteria |
|-------|----------|
| **4** | SAST + dependency scanning in CI/CD with security gates blocking on critical findings; container scanning if applicable. |
| **3** | At least one scanning tool in CI/CD but missing container scanning or no blocking gate. |
| **2** | Dependency scanning configured (e.g., Dependabot) but no SAST; or scanning not integrated into pipeline. |
| **1** | No security scanning in CI/CD pipeline. |

> **Look for:** SonarQube, Semgrep, CodeGuru Reviewer in CI/CD; Dependabot config; `npm audit` or `pip-audit` in pipeline; ECR image scanning; `.snyk` policy files.


### Step 6: Operations & Observability (OPS-Q1 through OPS-Q9)

These questions evaluate the operational maturity and observability practices that support reliable, evolvable systems. Before evaluating each question, check the N/A mapping for the resolved `repo_type`. If the question is N/A, record it in the N/A display format and skip evaluation.

#### OPS-Q1: Distributed Tracing

**Question:** Is distributed tracing (X-Ray, OpenTelemetry, or partner solution) instrumented with trace ID propagation across service boundaries?

**Why it matters:** Without end-to-end tracing, debugging failures across service boundaries is guesswork. Distributed tracing is foundational for understanding request flows, identifying bottlenecks, and diagnosing production issues in any distributed system.

| Score | Criteria |
|-------|----------|
| **4** | End-to-end distributed tracing with propagated trace IDs across all service boundaries. |
| **3** | Tracing on primary services; some gaps in propagation. |
| **2** | Basic tracing on individual services but no cross-service propagation. |
| **1** | No distributed tracing instrumented. |

> **Look for:** OpenTelemetry SDK in dependency manifests, X-Ray instrumentation, traceparent/X-Amzn-Trace-Id header propagation.

#### OPS-Q2: SLO Definitions

**Question:** Are SLOs defined for critical user journeys?

**Why it matters:** Without SLOs, you cannot measure whether the system is meeting user expectations or degrading over time. SLOs drive prioritization of operational improvements and modernization investments.

| Score | Criteria |
|-------|----------|
| **4** | SLOs defined and monitored for all critical user-facing journeys with error budgets. |
| **3** | SLOs defined for primary journeys; monitoring in place but no error budget tracking. |
| **2** | Basic availability/latency alarms but no formal SLO definitions. |
| **1** | No SLOs — no formal definition of acceptable service levels. |

> **Look for:** SLO definitions in code or config; CloudWatch alarms on p99/p95 latency; error budget tracking; SLO dashboards.

#### OPS-Q3: Business Metrics

**Question:** Are custom metrics published for business outcomes, not just infrastructure metrics?

**Why it matters:** Infrastructure metrics (CPU, memory) tell you if the system is running, not if it's delivering value. Business metrics (conversion rates, resolution times, error rates by feature) drive informed modernization decisions.

| Score | Criteria |
|-------|----------|
| **4** | Business outcome metrics published alongside infrastructure metrics with dashboards. |
| **3** | Some business metrics tracked but not systematically across all features. |
| **2** | Infrastructure metrics only with ad hoc business reporting. |
| **1** | No custom metrics — only default CloudWatch infrastructure metrics. |

> **Look for:** `cloudwatch.put_metric_data` for business events; custom dashboards; business KPI alarms.

#### OPS-Q4: Anomaly Detection and Alerting

**Question:** Is there anomaly detection or alerting on error rates and latency?

**Why it matters:** Static threshold-based alerting misses gradual degradation and novel failure modes. Anomaly detection catches unexpected behavior patterns that fixed thresholds cannot.

| Score | Criteria |
|-------|----------|
| **4** | Anomaly detection enabled on error rates and latency for all critical paths. |
| **3** | Anomaly detection on primary paths; static thresholds on secondary paths. |
| **2** | Static threshold alarms only (e.g., CPU > 80%, error rate > 5%). |
| **1** | No alerting configured. |

> **Look for:** CloudWatch anomaly detection; error rate alarms; latency p99 alarms; PagerDuty/OpsGenie integration; composite alarms.

#### OPS-Q5: Deployment Strategy

**Question:** Is the deployment strategy blue/green, canary, or straight to production?

**Why it matters:** Direct-to-production deployments with no staged rollout eliminate the window to catch regressions before they affect all users. Canary and blue/green deployments enable safe, incremental releases.

| Score | Criteria |
|-------|----------|
| **4** | Canary or blue/green deployments; no direct-to-production releases. |
| **3** | Blue/green for primary services; direct deployment for auxiliary services. |
| **2** | Rolling deployments with basic health checks but no traffic shifting. |
| **1** | Direct-to-production deployment with no staged rollout. |

> **Look for:** CodeDeploy deployment config; Helm canary; Argo Rollouts; Lambda traffic shifting; ALB weighted target groups; feature flags.

#### OPS-Q6: Integration Testing

**Question:** Are there integration tests for critical workflows that run in the CI pipeline?

**Why it matters:** Unit tests alone don't catch integration failures — broken API contracts, database schema drift, or misconfigured infrastructure. Integration tests validate that the system works end-to-end.

| Score | Criteria |
|-------|----------|
| **4** | Integration test suites covering all critical workflows, run in CI pipeline. |
| **3** | Integration tests for primary workflows; some gaps in coverage. |
| **2** | Some integration tests but not run consistently in CI. |
| **1** | No integration tests — only unit tests or no automated tests at all. |

> **Look for:** Integration test directories; test containers; pytest-integration; API test suites (Postman/Newman); contract tests; end-to-end test pipelines in CI.

#### OPS-Q7: Incident Response Automation

**Question:** Are incident response workflows automated, and do runbooks exist in machine-readable or structured form?

**Why it matters:** Manual incident response is slow and error-prone. Automated runbooks and self-healing patterns reduce mean-time-to-recovery and free teams to focus on prevention rather than firefighting.

| Score | Criteria |
|-------|----------|
| **4** | Self-healing automation resolves a defined class of incidents without human intervention; runbooks are versioned and machine-readable. |
| **3** | Automated runbooks for common incidents; manual escalation for complex ones. |
| **2** | Runbooks exist as documentation but are not automated. |
| **1** | No runbooks — incident response is entirely ad hoc. |

> **Look for:** Runbook files (markdown, YAML, JSON); Systems Manager Automation documents; Lambda-based remediation; Step Functions for incident workflows; self-healing patterns.

#### OPS-Q8: Observability Ownership

**Question:** Does the application have defined observability ownership — service-level dashboards, alarms with named owners, and SLO definitions tied to specific teams?

**Why it matters:** Without clear ownership of observability assets, monitoring gaps emerge. Detecting whether the repo has CODEOWNERS for observability configs, named alarm owners, or team-specific dashboards signals operational maturity.

| Score | Criteria |
|-------|----------|
| **4** | Per-service dashboards and alarms with named owners; SLO definitions with team attribution. |
| **3** | Dashboards and alarms exist for most services; some gaps in ownership attribution. |
| **2** | Ad hoc observability — alarms exist but no clear ownership or team attribution. |
| **1** | No observability ownership — monitoring is reactive and fragmented. |

> **Look for:** SLO definition files with named owners; CODEOWNERS referencing observability assets; per-service dashboards and alarms; team tags on CloudWatch resources.

#### OPS-Q9: Resource Tagging Governance

**Question:** Are AWS resources consistently tagged for cost allocation, ownership, and environment identification?

**Why it matters:** Without consistent tagging, organizations cannot track costs per workload, identify resource ownership during incidents, or enforce budget controls. Tagging is foundational to cloud financial management and blast radius analysis. (WAF: COST 1-3)

| Score | Criteria |
|-------|----------|
| **4** | All resources tagged with consistent keys; tag enforcement via Config rules or SCPs; cost allocation tags activated. |
| **3** | Most resources tagged but inconsistent key naming or missing on some resource types; no enforcement. |
| **2** | Some resources tagged but many untagged; no tagging standard. |
| **1** | No tags found on resources; or only Name tags with no cost/ownership attribution. |

> **Look for:** `default_tags` in Terraform provider; `tags` on resources; `required-tags` Config rules; tag policies in AWS Organizations.


### Step 7: Evaluate AWS Modernization Pathways

After scoring all 37 questions in Steps 2–6, evaluate each of the 7 AWS Modernization Pathways. Each pathway has defined trigger conditions mapped to specific MOD question IDs and contextual guards that prevent false positives. Multiple pathways can be triggered simultaneously.

For each pathway, determine its status:

- **Triggered** — All trigger conditions are met AND the contextual guard does not prevent it.
- **Not Triggered** — One or more trigger conditions are not met, or the contextual guard prevents it.
- **Not Applicable** — The pathway is in the N/A pathway set for the detected `repo_type` (see N/A Pathway Mappings in the N/A Mapping section above).

#### 7.0 Check N/A Pathway Mappings

Before evaluating any pathway, check the `repo_type` against the N/A Pathway Mappings table. If a pathway is N/A for the detected repo_type, record it directly in the pathway summary table as:

| Field | Value |
|-------|-------|
| **Status** | Not Applicable |
| **Reason** | This is a `{repo_type}` repository. This pathway does not apply. |
| **Priority** | — |
| **Est. Effort** | — |

Do not evaluate trigger conditions for N/A pathways. Proceed to evaluate only the applicable pathways below.

#### 7.1 Move to Cloud Native

**Pathway:** Decompose monolith applications into loosely coupled distributed architectures using microservices, serverless, and event-driven patterns.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | APP-Q2 | < 3 | Application is a monolith or tightly coupled — not yet decomposed into independently deployable services. |
| Supporting | INF-Q1 | < 3 | Compute is primarily EC2-based with limited managed container orchestration or serverless adoption. |
| Supporting | APP-Q3 | < 3 | Inter-service communication is primarily synchronous HTTP with limited async patterns. |
| Supporting | APP-Q4 | < 3 | Long-running operations are handled synchronously with no async job processing. |

**Trigger Logic:** Triggered when APP-Q2 < 3 (primary trigger) AND at least one supporting condition is also met (INF-Q1 < 3, APP-Q3 < 3, or APP-Q4 < 3).

**Contextual Guard:** None — if the application is a monolith with supporting infrastructure gaps, this pathway is relevant regardless of other factors.

**Priority:** High — monolith decomposition is typically the highest-impact modernization initiative.
**Est. Effort:** High — decomposition requires architectural redesign, service boundary identification, data separation, and incremental migration.

**When Triggered, Include in Pathway Detail Section:**
- Current architecture state (monolith type, coupling level from APP-Q2 finding)
- Compute model gaps (from INF-Q1 finding)
- Communication pattern gaps (from APP-Q3, APP-Q4 findings)
- Recommended decomposition approach (link to Decomposition Strategy section if APP-Q2 < 3)
- Representative AWS services: Lambda, API Gateway, Step Functions, EventBridge, ECS/EKS
- Recommended patterns: Strangler Fig, Anti-corruption Layer, Event Sourcing, Saga
- Links to AWS prescriptive guidance for monolith decomposition

#### 7.2 Move to Containers

**Pathway:** Containerize existing workloads running on EC2/VMs and adopt fully managed container orchestration.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q1 | < 3 | Compute is primarily EC2/VM-based with no managed container orchestration or serverless. |
| Supporting | Discovery | No container definitions | No Dockerfile, docker-compose.yml, or Kubernetes manifests found during Step 1 discovery scan. |

**Trigger Logic:** Triggered when INF-Q1 < 3 AND no container definitions were found in the discovery scan.

**Contextual Guard:** This pathway SHALL NOT trigger if compute is already Lambda, Fargate, or ECS. Specifically:
- If INF-Q1 finding indicates compute is already running on ECS, EKS, Fargate, or Lambda, this pathway is **Not Triggered** even if INF-Q1 scores < 3 (e.g., a mix of managed and EC2 scoring a 2 would not trigger if the managed portion is already containerized).
- The guard prevents recommending containerization to workloads that have already moved beyond EC2/VM-based compute.

**Priority:** Medium — containerization is a foundational step that enables further modernization but is not as architecturally impactful as decomposition.
**Est. Effort:** Medium — requires creating Dockerfiles, container orchestration configs, and updating CI/CD pipelines, but does not require architectural redesign.

**When Triggered, Include in Pathway Detail Section:**
- Current compute model (from INF-Q1 finding — EC2 instance types, AMIs, auto-scaling groups)
- Container readiness indicators (application dependencies, port bindings, config externalization)
- Recommended container orchestration platform (respect `preferences` — e.g., if `prefer: ["eks"]`, recommend EKS; if `avoid: ["serverless"]`, do not recommend Fargate)
- Representative AWS services: ECS, EKS, Fargate, ECR, App Runner
- Migration approach: lift-and-containerize vs refactor-then-containerize
- Links to AWS container migration guidance

#### 7.3 Move to Open Source

**Pathway:** Migrate from commercial database engines and licensed software to open-source alternatives to reduce licensing costs and increase flexibility.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | DATA-Q4 | < 3 | Application relies on stored procedures, triggers, or proprietary SQL constructs (T-SQL, PL/SQL) that couple business logic to a commercial database engine. |
| Supporting | INF-Q2 | Finding | INF-Q2 finding mentions commercial database engines — Oracle, SQL Server, or other licensed database products detected in IaC or connection strings. |

**Trigger Logic:** Triggered when DATA-Q4 < 3 AND commercial database engines are detected in the INF-Q2 finding or discovery scan.

**Contextual Guard:** None — if proprietary SQL and commercial engines are detected, migration to open source is relevant regardless of other factors.

**Priority:** Medium — licensing cost reduction is significant but migration complexity depends on stored procedure density and proprietary SQL usage.
**Est. Effort:** High — requires schema conversion (AWS SCT), stored procedure extraction to application layer, query rewriting, and thorough regression testing.

**When Triggered, Include in Pathway Detail Section:**
- Commercial engines detected (from INF-Q2 finding — Oracle, SQL Server, etc.)
- Stored procedure and proprietary SQL density (from DATA-Q4 finding)
- Database engine versions and EOL status (from DATA-Q3 finding)
- Recommended migration targets (respect `preferences` — e.g., if `prefer: ["aurora"]`, recommend Aurora PostgreSQL/MySQL)
- Representative AWS services: RDS PostgreSQL, RDS MySQL, RDS MariaDB, Aurora, Amazon Linux, EKS
- Migration tools: AWS Schema Conversion Tool (SCT), AWS Database Migration Service (DMS)
- Links to AWS database migration prescriptive guidance

#### 7.4 Move to Managed Databases

**Pathway:** Migrate from self-managed databases (on EC2, containers, or on-premises) to fully managed, purpose-built cloud-native database services.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q2 | < 3 | Databases are self-managed — running on EC2, in containers, or on-premises with manual patching, backup, and scaling. |
| Supporting | DATA-Q3 | < 3 | Database engine versions are unpinned, approaching EOL, or at EOL — indicating lack of lifecycle management. |

**Trigger Logic:** Triggered when INF-Q2 < 3 (self-managed databases detected). DATA-Q3 < 3 strengthens the case but is not required.

**Contextual Guard:** None — if databases are self-managed, migration to managed services is relevant regardless of other factors.

**Priority:** High — self-managed databases are a significant operational burden and a common source of incidents.
**Est. Effort:** Medium — managed database migration is well-tooled (DMS/SCT) but requires downtime planning, connection string updates, and validation.

**When Triggered, Include in Pathway Detail Section:**
- Current database topology (from INF-Q2 finding — self-managed engines, hosting model)
- Engine versions and EOL status (from DATA-Q3 finding)
- Data access patterns (from DATA-Q2 finding — centralized vs scattered)
- Recommended managed database targets (respect `preferences` — e.g., if `prefer: ["aurora"]`, recommend Aurora; if `avoid: ["dynamodb"]`, do not recommend DynamoDB)
- Representative AWS services: Aurora, RDS, DynamoDB, DocumentDB, ElastiCache, MemoryDB, OpenSearch Service
- Migration tools: AWS DMS, AWS SCT
- Links to AWS managed database migration guidance

#### 7.5 Move to Managed Analytics

**Pathway:** Migrate from self-managed streaming, ETL, and analytics infrastructure to fully managed, cost-optimized data lake and real-time analytics services.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q4 | < 3 | Messaging and streaming infrastructure is self-managed (Kafka on EC2, RabbitMQ in containers) or absent entirely. |
| Supporting | Discovery | Data source sprawl | Multiple data sources detected with no unified access layer (DATA-Q2 finding indicates scattered data access). |

**Trigger Logic:** Triggered when INF-Q4 < 3 AND evidence of data processing workloads exists in the discovery scan.

**Contextual Guard:** Evidence of data processing workloads MUST exist. This pathway SHALL NOT trigger if:
- No streaming, ETL, data pipeline, or analytics artifacts were found during discovery (Step 1).
- The application has no data processing responsibilities (e.g., a simple CRUD API with no analytics or streaming needs).

The guard prevents recommending managed analytics infrastructure to applications that do not process, transform, or analyze data at scale.

**Priority:** Medium — managed analytics reduces operational overhead for data-intensive workloads but is not relevant for all applications.
**Est. Effort:** Medium to High — depends on the complexity of existing streaming/ETL infrastructure and the volume of data pipelines to migrate.

**When Triggered, Include in Pathway Detail Section:**
- Current streaming/messaging infrastructure (from INF-Q4 finding — self-managed Kafka, RabbitMQ, etc.)
- Data access patterns and sprawl (from DATA-Q2 finding)
- Data processing workloads identified during discovery (ETL scripts, pipeline definitions, Glue jobs, Airflow DAGs)
- Recommended managed analytics targets (respect `preferences`)
- Representative AWS services: Redshift, Kinesis Data Streams, MSK Serverless, Athena, Lake Formation, Glue, QuickSight
- Links to AWS analytics modernization guidance

#### 7.6 Move to Modern DevOps

**Pathway:** Adopt modern development philosophies, practices, and tools for high-velocity, safe, and automated application delivery.

**Trigger Conditions:**

| Condition | Question ID | Threshold | Description |
|-----------|-------------|-----------|-------------|
| Primary | INF-Q10 | < 3 | Low IaC coverage — significant infrastructure is manually created (ClickOps). |
| Primary | INF-Q11 | < 3 | No CI/CD automation — deployments are manual or semi-manual. |
| Supporting | OPS-Q5 | < 3 | No canary or blue/green deployment strategy — direct-to-production releases. |
| Supporting | OPS-Q6 | < 3 | No integration tests in the CI pipeline. |

**Trigger Logic:** Triggered when at least one primary condition is met (INF-Q10 < 3 OR INF-Q11 < 3). Supporting conditions (OPS-Q5 < 3, OPS-Q6 < 3) strengthen the case and expand the scope of recommendations.

**Contextual Guard:** None — if IaC coverage or CI/CD automation is lacking, modern DevOps practices are universally relevant.

**Priority:** High — DevOps maturity is foundational to all other modernization pathways. Without automated pipelines and IaC, other modernization efforts are harder to execute safely.
**Est. Effort:** Medium — IaC adoption and CI/CD pipeline creation are well-understood practices with extensive tooling and guidance.

**When Triggered, Include in Pathway Detail Section:**
- Current IaC coverage (from INF-Q10 finding — percentage of infrastructure in code vs manual)
- Current CI/CD state (from INF-Q11 finding — pipeline stages, automation level)
- Deployment strategy gaps (from OPS-Q5 finding)
- Testing gaps (from OPS-Q6 finding)
- Recommended DevOps toolchain (respect `preferences`)
- Representative AWS services: CodeCommit, CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK, Proton, X-Ray, CloudWatch
- Links to AWS DevOps prescriptive guidance

#### 7.7 Move to AI

**Pathway:** Leverage AWS AI services to transform applications with AI capabilities, bridging traditional modernization and AI-driven computing. This pathway evaluates whether the application has adopted AI/agent frameworks, vector databases, RAG patterns, or agent evaluation infrastructure.

**Trigger Conditions:**

| Condition | Source | Description |
|-----------|--------|-------------|
| Primary | Discovery (Step 1) | No AI/agent framework usage detected — no imports of Bedrock SDK, LangChain, Strands, OpenAI, Spring AI, HuggingFace, or SageMaker SDK in source code. |
| Supporting | Discovery (Step 1) | No vector database or embeddings infrastructure detected — no OpenSearch with vector engine, Pinecone, pgvector, Weaviate, or Qdrant. |
| Supporting | Discovery (Step 1) | No RAG implementation detected — no embedding generation, vector store queries, or retrieval chain patterns. |
| Supporting | Discovery (Step 1) | No agent evaluation framework detected — no Ragas, DeepEval, or custom eval harness. |

**Trigger Logic:** Triggered when the primary condition is met (no AI/agent frameworks detected). Supporting conditions strengthen the case and expand the scope of recommendations.

**Contextual Guard:** Requires explicit AI/agent/LLM intent in the portfolio or service context. Before evaluating primary trigger conditions, scan both the portfolio-level `context` and the service-level `context` (from `additionalPlanContext`) for AI-related signal terms.

**AI-Related Signal Terms (case-insensitive):**
"AI", "agent", "agentic", "LLM", "machine learning", "ML", "Bedrock", "generative", "GenAI", "RAG", "vector", "embedding", "copilot", "assistant", "chatbot", "autonomous"

**Guard Logic:**

```
ai_signals = ["AI", "agent", "agentic", "LLM", "machine learning", "ML", 
              "Bedrock", "generative", "GenAI", "RAG", "vector", "embedding",
              "copilot", "assistant", "chatbot", "autonomous"]

portfolio_context = additionalPlanContext.context  # portfolio-level
service_context = additionalPlanContext.context     # service-level (from repo config)

has_ai_intent = false
for signal in ai_signals:
    if signal in portfolio_context (case-insensitive) OR signal in service_context (case-insensitive):
        has_ai_intent = true
        break

if not has_ai_intent:
    pathway_status = "Not Triggered"
    reason = "No AI/agent intent detected in portfolio or service context."
else:
    # Proceed with primary trigger evaluation (no AI frameworks detected)
    evaluate_primary_triggers()
```

If neither the portfolio-level context nor the service-level context contains any of the 17 AI-related signal terms, the pathway status is set to **Not Triggered** with reason: "No AI/agent intent detected in portfolio or service context." The primary trigger conditions are not evaluated. When at least one context string contains an AI-related signal and the primary trigger conditions are met, the pathway status is set to **Triggered**.

**Priority:** Medium — AI adoption is increasingly important but depends on the application's domain and use cases.
**Est. Effort:** Medium — initial AI integration (e.g., adding Bedrock for a single use case) is moderate effort, but building comprehensive AI infrastructure (vector DBs, RAG, eval frameworks) requires more investment.

**When Triggered, Include in Pathway Detail Section:**
- Current AI/agent infrastructure state (from discovery — what was and was not found)
- Application domain and potential AI use cases based on assessment findings
- Quick wins: identify immediate AI integration opportunities (link to Quick Agent Wins section)
- Recommended AI services (respect `preferences`)
- Representative AWS services: Amazon Bedrock, Amazon Bedrock AgentCore, Amazon Q, SageMaker, OpenSearch Service (vector engine), Amazon Kendra
- Foundation requirements: what needs to be in place before AI integration (API surface, data access, observability)
- Links to AWS AI/ML prescriptive guidance

---

### Pathway Summary Table

After evaluating all 7 pathways, compile the results into a summary table. All 7 pathways MUST appear in this table regardless of status. This table appears in the report output before the pathway detail subsections.

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 2 | Move to Containers | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 3 | Move to Open Source | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 4 | Move to Managed Databases | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 5 | Move to Managed Analytics | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 6 | Move to Modern DevOps | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |
| 7 | Move to AI | {Triggered / Not Triggered / Not Applicable} | {High / Medium / Low / —} | {High / Medium / Low / —} | {Question IDs and scores that triggered it, or reason for Not Triggered / Not Applicable} |

**Status values:**
- **Triggered** — All trigger conditions met and contextual guard does not prevent it. Include priority, effort, and key trigger criteria.
- **Not Triggered** — One or more trigger conditions not met, or contextual guard prevents it. Set priority and effort to "—". Key trigger criteria should explain why it was not triggered (e.g., "INF-Q1 = 4 — compute already on managed services").
- **Not Applicable** — Pathway is N/A for the detected `repo_type`. Set priority and effort to "—". Key trigger criteria should state: "This is a `{repo_type}` repository. This pathway does not apply."

**Pathway Detail Subsections:**
After the summary table, include a detailed subsection for each **Triggered** pathway only. Each detail subsection should contain the content specified in the "When Triggered, Include in Pathway Detail Section" guidance for that pathway above. Do not include detail subsections for Not Triggered or Not Applicable pathways.


### Step 8: Decomposition Strategy (Conditional — APP-Q2 < 3)

This section is **conditional**. Include it in the report ONLY when APP-Q2 (Monolith vs Microservices) scores less than 3. If APP-Q2 >= 3, skip this section entirely — the application is already decomposed or has well-defined module boundaries, and decomposition guidance is not needed.

When APP-Q2 < 3, the application is a monolith or tightly coupled system that would benefit from decomposition. This section provides concrete approach options, pattern recommendations, and effort estimates to guide the modernization strategy.

#### 8.1 Decomposition Approach Options

Evaluate the monolith's characteristics (from APP-Q2 finding, DATA-Q2 finding, and discovery evidence) and recommend one of the following approaches:

| Approach | Description | When to Use | Level of Effort | Recommendation |
|----------|-------------|-------------|-----------------|----------------|
| **Strangler Fig (Parallel Track)** | Incrementally extract services from the monolith while keeping the monolith running. New features are built as services; existing features are migrated over time. The monolith shrinks as services grow. | APP-Q2 = 2 (identifiable modules with coupling). The monolith has recognizable boundaries that can be extracted one at a time. Team can sustain parallel development. | **Medium to High** — 6-18 months depending on monolith size. Each extraction is a bounded effort. | ✅ **Recommended for most monoliths.** Lowest risk, incremental value delivery, no big-bang cutover. |
| **Conditional / Adaptive** | Start with containerizing the monolith as-is (lift-and-containerize), then selectively extract high-value services based on business priority. Not all modules need to become services — some may remain in the monolith permanently. | APP-Q2 = 2 and the team has limited capacity for full decomposition. Business pressure requires quick wins before full architectural change. | **Low to Medium** — containerization in 2-4 weeks, selective extraction over 3-12 months. | ✅ **Recommended when capacity is constrained** or when only specific modules need independent scaling/deployment. |
| **Big-Bang Rewrite** | Rewrite the entire application as microservices from scratch, replacing the monolith in a single cutover. | Almost never. Only when the monolith is so degraded (APP-Q2 = 1, no identifiable modules, pervasive shared state) that incremental extraction is impossible. | **Very High** — 12-24+ months. High risk of scope creep, feature parity gaps, and failed cutover. | ⚠️ **Recommended against.** High risk of failure. If the monolith is functional, Strangler Fig or Conditional approaches are safer. Only consider if the monolith is truly unmaintainable. |

#### 8.2 Pattern Recommendations

When decomposing a monolith, apply these architectural patterns to manage the transition safely. Each pattern is linked to AWS prescriptive guidance:

| Pattern | Purpose | When to Apply | AWS Prescriptive Guidance |
|---------|---------|---------------|---------------------------|
| **Anti-corruption Layer (ACL)** | Isolate the new service from the monolith's data model and API contracts. Prevents the monolith's design decisions from leaking into new services. | Every extraction — place an ACL between the new service and the monolith to translate between their models. | [Strangler Fig pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html) |
| **Saga Pattern** | Manage distributed transactions across services that were previously handled by a single database transaction in the monolith. | When extracting modules that participate in multi-step business transactions (e.g., order → payment → inventory). | [Saga pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html) |
| **Event Sourcing** | Capture all changes as a sequence of events rather than storing only current state. Enables audit trails, temporal queries, and event-driven integration between services. | When the extracted service needs to maintain a history of state changes, or when multiple services need to react to the same business events. | [Event sourcing pattern](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html) |
| **Hexagonal Architecture (Ports and Adapters)** | Structure each new service with clear boundaries between business logic (core), external interfaces (ports), and infrastructure adapters. | Every new service — ensures the service is testable, portable, and decoupled from specific infrastructure choices. | [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |

#### 8.3 Effort Estimation Factors

The actual decomposition effort depends on these factors discovered during the assessment:

| Factor | Low Effort Signal | High Effort Signal | Source |
|--------|-------------------|-------------------|--------|
| Module boundaries | Clear package/module structure with minimal cross-dependencies | No clear boundaries, circular dependencies, pervasive shared state | APP-Q2 finding |
| Data coupling | Each module owns its data; minimal shared database tables | Single shared database with cross-module joins and shared mutable state | DATA-Q2 finding |
| Stored procedures | No stored procedures; all logic in application layer | Heavy stored procedure usage coupling logic to the database | DATA-Q4 finding |
| Communication patterns | Some async patterns already in place | All communication is synchronous HTTP | APP-Q3 finding |
| CI/CD maturity | Automated pipeline exists; can support multi-service deployment | Manual deployments; no pipeline to extend | INF-Q11 finding |
| Test coverage | Integration tests exist for critical workflows | No automated tests — regression risk during extraction | OPS-Q6 finding |

Use these factors to calibrate the effort estimate for the recommended approach. Include the calibrated estimate in the report.


### Step 9: Quick Agent Wins

Based on the assessment findings from Steps 2–6, identify agent opportunities that the current architecture can support. This section is discovery-based — it evaluates what the system already has in place and identifies where AI agents can deliver value with minimal additional investment.

**Inclusion Rule:** Only include a win where the system has sufficient foundation. These are not aspirational recommendations — they are actionable opportunities based on evidence found during the assessment. If the prerequisite condition is not met, do not include that win.

#### 9.1 Quick Agent Win Evaluation Table

For each potential win below, check the prerequisite condition against the assessment scores and discovery findings. Include the win in the report only if the condition is met.

| Prerequisite Condition | Suggested Agent Win | Why It Works Now |
|------------------------|---------------------|------------------|
| API docs exist (APP-Q5 >= 2) and structured JSON responses detected in discovery | **API-aware agent** that discovers and invokes existing endpoints as tools | Existing API surface provides the tool interface; agent can call endpoints without new development. |
| Database with clear, documented schema (DATA-Q2 >= 2) | **Data query agent** with natural language to SQL | Centralized data access layer provides a clean query interface; agent translates natural language to structured queries. |
| CI/CD pipeline exists (INF-Q11 >= 2) | **DevOps agent** that triggers deployments, checks build status, and manages releases | Existing pipeline provides the automation surface; agent orchestrates pipeline actions via API. |
| Documentation, README, or wiki content exists in repo (detected during discovery) | **RAG-based knowledge agent** using existing documentation as a knowledge base | Existing documentation provides the corpus; agent indexes and retrieves relevant content for developer questions. |
| Workflow orchestration in place (INF-Q3 >= 2) | **Workflow automation agent** that monitors and manages existing Step Functions or orchestration workflows | Existing orchestration provides the execution surface; agent monitors workflow state and triggers actions. |
| Structured logging and tracing in place (OPS-Q1 >= 2) | **Observability agent** that queries logs, traces incidents, and suggests root causes | Existing observability data provides the signal; agent correlates traces and logs to identify issues. |

#### 9.2 How to Present Quick Agent Wins

In the report, list only the wins where the prerequisite condition is met. For each included win:

1. State the prerequisite condition and the evidence that satisfies it (specific scores and discovery findings).
2. Describe the agent win and what it enables.
3. Note any additional steps needed to operationalize the win (e.g., "API docs exist but need OpenAPI spec generation for full tool discovery").
4. Estimate effort as **Low** (agent can use existing interfaces directly) or **Medium** (some preparation needed, such as generating API specs or indexing documentation).

If no prerequisite conditions are met, include a brief note: "No Quick Agent Wins identified. The system lacks the foundational capabilities (API documentation, CI/CD automation, structured logging) needed to support agent integration. Address the gaps identified in the assessment before pursuing agent opportunities."

These wins can be pursued in parallel with the modernization roadmap. They demonstrate agent value early while foundations are being improved.


### Step 10: AI/Agent Infrastructure Evaluation Logic

This section documents the evaluation logic that connects discovery findings (from Step 1) to the Move to AI pathway (Step 7.7) and the Quick Agent Wins (Step 9). The actual discovery scanning is performed in Step 1, and the Move to AI pathway evaluation is in Step 7.7. This section serves as a cross-reference explaining how AI/agent infrastructure signals flow through the assessment.

#### 10.1 AI/Agent Discovery Signals

During the discovery scan (Step 1), the following AI/agent infrastructure signals are identified and recorded in the file inventory:

| Signal Category | What to Look For | Discovery Evidence |
|-----------------|------------------|-------------------|
| **AI/Agent Frameworks** | Bedrock SDK imports, LangChain imports, Strands SDK imports, OpenAI SDK imports, Spring AI imports, HuggingFace imports, SageMaker SDK imports | Import statements in source code; framework dependencies in package manifests (e.g., `boto3` with `bedrock-runtime`, `langchain` in requirements.txt, `@aws-sdk/client-bedrock-runtime` in package.json, `spring-ai` in pom.xml) |
| **Vector Database Infrastructure** | OpenSearch with vector engine (`knn` plugin), Pinecone client imports, pgvector extension in PostgreSQL config, Weaviate client imports, Qdrant client imports | IaC resources for vector-capable databases; client library imports in source code; database configuration enabling vector extensions |
| **RAG Implementation** | Embedding generation calls, vector store query patterns, retrieval chain implementations, document chunking logic | Source code patterns: embedding API calls, similarity search queries, retrieval-augmented generation chains, document loaders and splitters |
| **Agent Evaluation Frameworks** | Ragas imports, DeepEval imports, custom evaluation harness patterns, LLM-as-judge implementations | Test files with evaluation framework imports; evaluation configuration files; benchmark datasets |

#### 10.2 How Discovery Signals Feed Downstream Steps

The AI/agent discovery signals recorded in Step 1 are consumed by two downstream steps:

**→ Move to AI Pathway (Step 7.7):**
- The Move to AI pathway's primary trigger condition checks whether AI/agent frameworks were found during discovery.
- If **no** AI/agent framework imports are detected, the primary trigger is met.
- Supporting conditions check for absence of vector DB infrastructure, RAG implementation, and agent evaluation frameworks.
- The pathway is triggered when the primary condition is met (no AI/agent frameworks), regardless of supporting conditions.
- See Step 7.7 for the complete trigger logic and contextual guard.

**→ Quick Agent Wins (Step 9):**
- Quick Agent Wins are evaluated based on assessment scores (Steps 2–6), not directly on AI/agent discovery signals.
- However, the presence of AI/agent infrastructure in discovery may indicate that some agent wins are already being pursued, which should be noted in the Quick Agent Wins section.
- If AI/agent frameworks are already present, the Quick Agent Wins section should acknowledge existing AI capabilities and focus on expansion opportunities rather than initial adoption.

#### 10.3 Cross-Reference Summary

| Assessment Step | Uses AI/Agent Discovery Signals? | How |
|-----------------|----------------------------------|-----|
| Step 1: Discovery | Produces signals | Scans for AI/agent frameworks, vector DBs, RAG patterns, eval frameworks |
| Steps 2–6: Question Evaluation | Indirectly | APP-Q1 finding may reference AI framework usage as part of language ecosystem evaluation |
| Step 7.7: Move to AI Pathway | Directly | Primary and supporting trigger conditions check for absence of AI/agent infrastructure |
| Step 9: Quick Agent Wins | Indirectly | Wins are based on assessment scores; existing AI infrastructure is noted as context |

This cross-reference ensures that AI/agent infrastructure evaluation is not duplicated across steps. The discovery scan (Step 1) is the single source of truth for what AI/agent artifacts exist. The Move to AI pathway (Step 7.7) and Quick Agent Wins (Step 9) consume those findings through their respective evaluation logic.



## Report Template

The assessment output is a structured Markdown report saved as `{repo-name}-mod-report.md`. The report MUST contain all sections listed below in the specified order. Every section is required unless explicitly marked as conditional.

### Report Section Order

1. **Metadata Header**
2. **Overall and Category Score Table**
3. **Top 5 Gaps**
4. **Quick Agent Wins**
5. **Pathway Summary Table** (all 7 pathways)
6. **Pathway Detail Subsections** (triggered pathways only)
7. **Decomposition Strategy** (conditional — only when APP-Q2 < 3)
8. **Detailed Findings for All 37 Questions**
9. **Learning Materials**
10. **Evidence Index**

---

### Section 1: Metadata Header

```markdown
# Modernization Readiness Assessment Report

| Field | Value |
|-------|-------|
| **Repository** | {repo-name} |
| **Date** | {assessment-date} |
| **Repo Type** | {repo_type} |
| **Priority** | {priority or "—" if not provided} |
| **Tags** | {tags as comma-separated list or "—" if not provided} |
| **Context** | {context or "—" if not provided} |
| **Overall Score** | {overall-score} / 4.0 |
```

If `repo_type` was not provided and defaulted to `application`, include a note: "Repo type defaulted to `application` (not specified in assessment context)."

If `repo_type` was provided but unrecognized, include a warning: "Unrecognized repo_type '{value}', defaulted to `application`."

### Section 2: Overall and Category Score Table

```markdown
## Score Summary

| Category | Score | Rating |
|----------|-------|--------|
| Infrastructure, Platform, and DevOps (INF) | {score} / 4.0 | {rating} |
| Application Architecture (APP) | {score} / 4.0 | {rating} |
| Data Platform Modernization (DATA) | {score} / 4.0 | {rating} |
| Security Baseline (SEC) | {score} / 4.0 | {rating} |
| Operations & Observability (OPS) | {score} / 4.0 | {rating} |
| **Overall** | **{score} / 4.0** | **{rating}** |
```

**Rating labels:**

| Score Range | Rating |
|-------------|--------|
| 3.5 – 4.0 | ✅ Mature |
| 2.5 – 3.4 | 🟡 Partial |
| 1.5 – 2.4 | 🟠 Needs Work |
| < 1.5 | ❌ Not Present |

If a category score is "N/A" (all questions in that category are N/A for the detected repo_type), display:

```markdown
| Application Architecture (APP) | N/A | N/A — all questions not applicable for {repo_type} |
```

**Scoring rules:**
- Category score = arithmetic mean of non-N/A question scores in that category.
- Overall score = arithmetic mean of non-N/A category scores (each category weighted equally).
- N/A questions excluded from both numerator and denominator.
- If all questions in a category are N/A, category score = "N/A", excluded from overall average.

### Section 3: Top 5 Gaps

```markdown
## Top 5 Gaps

| # | Question | Score | Gap Summary | Impact |
|---|----------|-------|-------------|--------|
| 1 | {question-id}: {question-title} | {score} | {one-line gap description} | {impact on modernization} |
| 2 | ... | ... | ... | ... |
| 3 | ... | ... | ... | ... |
| 4 | ... | ... | ... | ... |
| 5 | ... | ... | ... | ... |
```

Select the 5 questions with the lowest scores (excluding N/A). Break ties by prioritizing questions that trigger pathways. If fewer than 5 non-N/A questions have gaps (score < 4), include only those with gaps.

### Section 4: Quick Agent Wins

```markdown
## Quick Agent Wins

{Include only wins where the prerequisite condition is met, as evaluated in Step 9.}
```

For each included win, present:

```markdown
### {Win Name}

- **Prerequisite:** {condition and evidence}
- **What it enables:** {description}
- **Additional steps:** {any preparation needed}
- **Effort:** {Low / Medium}
```

If no wins are identified, include: "No Quick Agent Wins identified. The system lacks the foundational capabilities needed to support agent integration. Address the gaps identified in this assessment before pursuing agent opportunities."

### Section 5: Pathway Summary Table

```markdown
## AWS Modernization Pathways

| # | Pathway | Status | Priority | Est. Effort | Key Trigger Criteria |
|---|---------|--------|----------|-------------|---------------------|
| 1 | Move to Cloud Native | {status} | {priority} | {effort} | {criteria} |
| 2 | Move to Containers | {status} | {priority} | {effort} | {criteria} |
| 3 | Move to Open Source | {status} | {priority} | {effort} | {criteria} |
| 4 | Move to Managed Databases | {status} | {priority} | {effort} | {criteria} |
| 5 | Move to Managed Analytics | {status} | {priority} | {effort} | {criteria} |
| 6 | Move to Modern DevOps | {status} | {priority} | {effort} | {criteria} |
| 7 | Move to AI | {status} | {priority} | {effort} | {criteria} |
```

All 7 pathways MUST appear in this table. Status values: Triggered, Not Triggered, Not Applicable.

### Section 6: Pathway Detail Subsections

For each **Triggered** pathway, include a detail subsection with the content specified in Step 7 ("When Triggered, Include in Pathway Detail Section"). Do not include detail subsections for Not Triggered or Not Applicable pathways.

```markdown
### Pathway: {Pathway Name}

**Status:** Triggered
**Priority:** {High / Medium / Low}
**Estimated Effort:** {High / Medium / Low}

{Pathway-specific detail content as specified in Step 7}
```

### Section 7: Decomposition Strategy (Conditional)

**Include this section ONLY when APP-Q2 < 3.** If APP-Q2 >= 3, omit this section entirely.

```markdown
## Decomposition Strategy

{Content from Step 8 — approach options, pattern recommendations, effort estimation}
```

### Section 8: Detailed Findings for All 37 Questions

```markdown
## Detailed Findings

### Infrastructure, Platform, and DevOps

#### INF-Q1: Managed Compute

| Field | Value |
|-------|-------|
| **Score** | {1-4 or N/A} |
| **Finding** | {What was discovered — cite specific files and resources} |
| **Gap** | {What's missing or needs improvement, or N/A} |
| **Recommendation** | {Specific action to close the gap, or N/A} |
| **Evidence** | {File paths and resource names cited} |

{Repeat for all 37 questions across all 5 sections}
```

**All 37 questions MUST appear** in this section. N/A questions are listed using the N/A display format:

```markdown
| Field | Value |
|-------|-------|
| **Score** | N/A |
| **Finding** | This is a `{repo_type}` repository. This question does not apply. |
| **Gap** | N/A |
| **Recommendation** | N/A |
| **Evidence** | N/A |
```

Questions are grouped by section in the same order as the evaluation steps:
1. Infrastructure, Platform, and DevOps (INF-Q1 through INF-Q11)
2. Application Architecture (APP-Q1 through APP-Q6)
3. Data Platform Modernization (DATA-Q1 through DATA-Q4)
4. Security Baseline (SEC-Q1 through SEC-Q7)
5. Operations & Observability (OPS-Q1 through OPS-Q9)

### Section 9: Learning Materials

```markdown
## Learning Materials

Include relevant links based on triggered pathways. Only include learning materials for pathways with status "Triggered."
```

| Pathway | Learning Resources |
|---------|-------------------|
| **Move to Cloud Native** | [AWS Modernization Pathways: Move to Cloud Native Serverless](https://skillbuilder.aws/learning-plan/CMK2J48MVN) · [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html) |
| **Move to Containers** | [Move to Containers with Amazon EKS](https://skillbuilder.aws/learning-plan/GNYBZ9X9EM) · [Move to Containers with Amazon ECS](https://skillbuilder.aws/learning-plan/CDA8Y4JRRR) · [EKS Workshop](https://www.eksworkshop.com/) |
| **Move to Open Source** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) (covers open source engine migration) |
| **Move to Managed Databases** | [Move to Managed Databases](https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC) · [AWS DMS Getting Started](https://skillbuilder.aws/learn/ND246G8Y3W) |
| **Move to Managed Analytics** | [Move to Managed Analytics](https://skillbuilder.aws/learning-plan/RWZA84NMVV) |
| **Move to Modern DevOps** | [Move to Modern DevOps](https://skillbuilder.aws/learning-plan/1FGEQKGPQD) · [Getting Started with DevOps on AWS](https://skillbuilder.aws/learn/R4B13K95YQ) |
| **Move to AI** | [Move to AI](https://skillbuilder.aws/learning-plan/VDFEE4ACCV) · [Amazon Bedrock Getting Started](https://skillbuilder.aws/learn/63KTRM86DQ) · [Introduction to Agentic AI on AWS](https://skillbuilder.aws/learn/DNBD5MT8ZD) |

If no pathways are triggered, include: "No pathways triggered — no pathway-specific learning materials applicable. Refer to the [AWS SkillBuilder](https://skillbuilder.aws/) catalog for general cloud architecture training."

### Section 10: Evidence Index

```markdown
## Evidence Index

| File Path | Referenced By | Context |
|-----------|--------------|---------|
| {relative/path/to/file} | {Question IDs that cite this file} | {Brief description of what this file evidences} |
| ... | ... | ... |
```

The evidence index compiles all file references cited across the detailed findings into a single lookup table. This enables reviewers to trace any finding back to the specific file that supports it.

Include every file path that appears in any finding's evidence field. Group by directory for readability if the list exceeds 20 entries.


## Constraints and Guardrails

The following constraints govern the assessment execution and report generation. These are non-negotiable rules that the evaluating agent MUST follow.

### C1: Read-Only Assessment

This assessment operates in **read-only mode**. The evaluating agent SHALL NOT:
- Modify any source code, configuration files, or infrastructure definitions in the repository.
- Create, delete, or rename any files in the repository (except the output report file).
- Execute any commands that change repository state (no `git commit`, no `terraform apply`, no `npm install`).

The only write operation permitted is creating the output report file (`{repo-name}-mod-report.md`).

### C2: All 37 Questions Must Appear in Report

Every one of the 37 questions MUST appear in the Detailed Findings section of the report, regardless of repo_type. Questions that are N/A for the detected repo_type are listed using the N/A display format — they are never omitted. This ensures the report is a complete record of all 37 evaluation criteria.

### C3: All 7 Pathways Must Appear in Pathway Table

Every one of the 7 AWS Modernization Pathways MUST appear in the Pathway Summary Table, regardless of status. Pathways that are Not Triggered or Not Applicable are listed with their respective status and reason — they are never omitted from the table.

### C4: Evidence-Based Findings

Every finding MUST cite specific evidence from the repository:
- **File paths** — Reference the specific files that support the finding (e.g., `terraform/main.tf`, `src/app/server.ts`, `.github/workflows/deploy.yml`).
- **Resource names** — Reference specific IaC resource names, service names, or configuration keys.
- **Absence is evidence** — If a search for specific artifacts finds nothing, that absence is itself a finding. State what was searched for and that it was not found (e.g., "No Dockerfile or container definitions found in the repository").

Do not make findings based on assumptions or general knowledge. Every score must be traceable to specific repository evidence or documented absence of evidence.

### C5: Honest Calibration

Scores MUST reflect genuine assessment of the repository evidence:
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
