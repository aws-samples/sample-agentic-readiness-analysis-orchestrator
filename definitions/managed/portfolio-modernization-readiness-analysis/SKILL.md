---
name: portfolio-modernization-readiness-analysis
description: Aggregates per-repo MOD reports into portfolio-level roadmap and cross-cutting analysis
type: managed
---

## Name

Portfolio Modernization Readiness Analysis

## Objective

Aggregate individual repository Modernization Readiness Analysis (MOD) reports into a portfolio-level analysis that identifies cross-cutting modernization gaps, constructs service dependency graphs with coupling analysis, generates dependency-aware phased roadmaps, aggregates pathway triggers, assesses portfolio-wide risk, and provides resource allocation and AWS program recommendations — enabling coordinated modernization planning across the entire service estate.

## Summary

This transformation consumes multiple individual MOD report JSON artifacts (`*-mod-report.json` files) from different repositories and produces a comprehensive portfolio-level modernization view. It performs intelligent discovery and parsing of MOD report JSONs, calculates portfolio-wide score averages and category breakdowns, summarizes the technology stack across the portfolio, constructs a service dependency graph with coupling scores and blast radius analysis, identifies two-tier cross-cutting concerns (Foundational Blockers and Improvement Opportunities), generates a dependency-aware four-phase roadmap, aggregates pathway triggers across services, identifies integration opportunities, performs risk analysis with a likelihood-impact matrix, provides resource allocation recommendations, recommends AWS engagement programs, curates learning materials, and produces a service-by-service summary.

The transformation follows these implementation steps:
1. **Read Context** (Step 0): Parse additionalPlanContext for portfolio framing, preferences, and dependency information
2. **Discovery** (Step 1): Locate all MOD report files in the directory structure
3. **Parsing** (Step 2): Extract scores, pathway data, findings, and technology stack from each report
4. **Executive Dashboard** (Step 3): Build portfolio score overview and category averages
5. **Technology Stack Summary** (Step 3b): Consolidate technology usage across the portfolio
6. **Service Dependency Map** (Step 4): Construct dependency graph with coupling scores, fan-in/fan-out, blast radius, and circular dependency detection
7. **Cross-Cutting Concerns** (Step 5): Identify two-tier cross-cutting gaps (Foundational Blockers and Improvement Opportunities)
8. **Infrastructure Cross-Referencing** (Step 5b): Cross-reference infra/deployment-config repo capabilities with application repo findings to identify false positives where capabilities exist in the portfolio but in separate repos
9. **Dependency-Aware Phased Roadmap** (Step 6): Generate 4-phase roadmap with dependency-based service ordering
10. **Pathway Aggregation** (Step 7): Aggregate pathway triggers across the portfolio
11. **Synthesis** (Step 8): Integration opportunities, risk analysis, resource allocation
12. **AWS Programs & Engagement Recommendations** (Step 9): Recommend MAP, MMP, WAMP, EBA, OLA, VMP, ISV WMP where triggered
13. **Portfolio-Level Questions** (Step 10): Evaluate PORT-MOD-Q1 through PORT-MOD-Q5 — capabilities only visible across multiple repos

The output is a **four-artifact bundle** (per the Four-Artifact Output Contract below) containing:
- `{portfolio_name}-portfolio-mod-report.md` — narrative prose report
- `{portfolio_name}-portfolio-mod-report.json` — canonical machine-readable contract
- `{portfolio_name}-portfolio-mod-report.html` — single self-contained HTML visualization
- `{portfolio_name}-portfolio-mod-report.metadata.json` — version compatibility sidecar

The MD report contains:
- Executive dashboard with portfolio score overview and category averages
- Technology stack summary
- Service dependency map with coupling scores, fan-in/fan-out, blast radius, circular dependencies
- Two-tier cross-cutting concerns (Foundational Blockers, Improvement Opportunities)
- Infrastructure cross-references (when infra/deployment-config repos exist in portfolio)
- Dependency-aware phased roadmap (4 fixed phases)
- Pathway aggregation across the portfolio
- Integration opportunities
- Risk analysis with likelihood-impact matrix
- Resource allocation recommendations
- AWS Programs & Engagement Recommendations (MAP, OLA, MMP, VMP, WAMP, EBA, ISV WMP)
- Learning materials mapped to portfolio skill gaps
- Service-by-service summary

This portfolio TD focuses on cross-cutting modernization concerns, dependency-aware roadmaps, and pathway aggregation. It does not include ARA readiness profiles or agent scope evaluation.

## Entry Criteria

- At least 2 individual MOD report JSON artifacts exist in repository directories
- MOD report JSONs follow the expected schema: `analysis_type == "mod"`, `overall_score` numeric, `categories[]`, `pathways[]` with all 7 pathways, `findings[]` array
- Reports are accessible at specified paths or in a common directory structure
- Write permissions exist to create the output directory and portfolio artifact bundle (MD, JSON, HTML, and metadata.json)

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning discovery, read the portfolio analysis context from `additionalPlanContext` to extract framing information, technology preferences, and service configuration.

#### 0.1 Read Portfolio Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `portfolio_name` | string | Yes | — | Identifier for the portfolio. Used to name the output bundle (`{portfolio_name}-portfolio-mod-report.{md,json,html,metadata.json}`) and to populate report headers and metadata. If absent, terminate with `"Portfolio analysis failed: portfolio_name is required in additionalPlanContext."` |
| `context` | string | No | — | Free-text description of the portfolio (e.g., "E-commerce platform with 5 microservices planning cloud-native modernization"). Used to frame portfolio-level recommendations and roadmap guidance. |
| `preferences` | object | No | — | Technology steering preferences with two arrays: `prefer` (technologies to favor in recommendations) and `avoid` (technologies to steer away from). Applied to portfolio-level technology recommendations, roadmap activities, and integration opportunity proposals. |
| `service_inventory` | object[] | No | — | List of services in the portfolio with metadata (name, path, priority, repo_type, tags, service_archetype). Used to enrich the service-by-service summary and cross-reference with discovered reports. `service_archetype` (optional, applies only to `application` repos) is passed through to each per-service MOD TD invocation to calibrate architecture-sensitive questions (INF-Q3, INF-Q4, APP-Q3, APP-Q4); if omitted, the service MOD TD auto-detects it. |
| `dependency_overrides` | object[] | No | — | Explicit service dependency declarations. Each entry has: `source` (service name), `target` (service name), `type` (sync, async, shared_db, shared_infra), and `description`. Used to build the service dependency graph in Step 4. |

**Example `additionalPlanContext`:**

```yaml
additionalPlanContext: |
  context: "E-commerce platform with 5 microservices planning cloud-native modernization"
  preferences:
    prefer: ["eks", "aurora", "graviton"]
    avoid: ["serverless", "dynamodb"]
  service_inventory:
    - name: "order-service"
      path: "../order-service"
      priority: "P0"
      repo_type: "application"
      service_archetype: "stateful-crud"
      tags: ["monolith", "php", "payment-critical"]
    - name: "catalog-service"
      path: "../catalog-service"
      priority: "P1"
      repo_type: "application"
      service_archetype: "data-gateway"
    - name: "infra-modules"
      path: "../infra-modules"
      priority: "P2"
      repo_type: "infrastructure-only"
  dependency_overrides:
    - source: "order-service"
      target: "catalog-service"
      type: "sync"
      description: "REST API call to look up product details"
    - source: "order-service"
      target: "payment-service"
      type: "sync"
      description: "Payment processing via REST"
    - source: "catalog-service"
      target: "inventory-db"
      type: "shared_db"
      description: "Shared PostgreSQL database for product catalog"
```

#### 0.2 Apply Defaults

- **`context`** → No default. If absent, portfolio-level recommendations are written without additional framing.
- **`preferences`** → No default. If absent, technology recommendations use neutral language without favoring or avoiding specific technologies.
- **`service_inventory`** → No default. If absent, service metadata is derived solely from discovered reports.
- **`dependency_overrides`** → No default. If absent, the service dependency map section notes that no dependency information was provided and recommends the user supply it for richer analysis.

#### 0.3 Fields NOT Read by This TD

The Portfolio MOD TD does **not** read, validate, or apply the following fields from `additionalPlanContext`. If present, they are ignored:

- **`agent_scope`** — Not used by this TD. Agent scope is an ARA-only concept.

#### 0.4 How Context Fields Are Used

Record the resolved values from Steps 0.1–0.2 in the analysis context. They will be used in subsequent steps as follows:

- **`context`** → Used throughout the report to frame findings, recommendations, and roadmap guidance with portfolio-specific context. For example, if context mentions "legacy PHP e-commerce", recommendations reference the specific technology stack and business domain.
- **`preferences`** → Used throughout the report to steer technology recommendations. When `prefer` contains values, recommendations favor those technologies where applicable (e.g., if `prefer: ["eks"]`, container recommendations reference EKS over ECS). When `avoid` contains values, recommendations steer away from those technologies (e.g., if `avoid: ["serverless"]`, recommendations do not suggest Lambda-based approaches). Preferences influence recommendation framing only — they do not change scores, N/A mappings, or pathway trigger logic.
- **`service_inventory`** → Used to enrich service metadata (priority, repo_type, tags, service_archetype) and cross-reference with discovered reports. When a service entry includes `service_archetype`, that value is passed through to the per-service MOD TD invocation for scoring calibration on architecture-sensitive questions. When absent, each service MOD TD auto-detects its own archetype.
- **`dependency_overrides`** → Used in Step 4 to construct the service dependency graph, and in Step 6 to generate the dependency-aware phased roadmap.


### Step 1: Discovery — Locate MOD Reports

Scan the target directory structure to find all individual MOD report JSON artifacts.

#### 1.1 Discovery Process

- Recursively search for files matching the pattern `*-mod-report.json` in the directory tree
- For each report found, extract the project/service name from the filename (the prefix before `-mod-report.json`)
- Extract the repository path (parent directory or grandparent directory of the report file)
- Create an inventory of all services assessed with their JSON file locations
- Validate minimum requirement: at least 2 reports must be discovered

**Input Options:**
- A parent directory containing multiple repository folders, each with a MOD report, OR
- A list of explicit paths to MOD report JSON files (from `service_inventory` paths)

#### 1.2 Validation

- Verify each discovered file exists and is readable
- Verify each file is a valid JSON document
- Verify each file is the expected MOD report shape:
  - Has `analysis_type == "mod"` at the root
  - Has `overall_score` numeric between 1.0 and 4.0
  - Has a `categories[]` array with entries for INF, APP, DATA, SEC, OPS
  - Has a `pathways[]` array with all 7 pathways
  - Has a `findings[]` array with question IDs (INF-Q1 through OPS-Q9) and the 12 per-finding fields
  - Has a `metadata` object with `analysis_type` and `td_version`
- Exclude files that don't match the expected shape — log a warning for each excluded file
- Log warnings for inaccessible or malformed files
- **Terminate with a clear error if fewer than 2 valid MOD reports are found**

#### 1.3 Build Report Inventory

After discovery, compile a structured inventory:

| Field | Source |
|-------|--------|
| Service name | Extracted from filename prefix (or `metadata.repo_name` if present) |
| Report file path | Full path to the `*-mod-report.json` file |
| Repository path | Parent directory of the report |
| Priority | From `service_inventory` if available, otherwise from `metadata.priority` in the JSON if present |
| Repo type | From `metadata.repo_type` in the JSON |
| Tags | From `service_inventory` if available, otherwise from `metadata.tags` in the JSON if present |

Cross-reference discovered reports with `service_inventory` (if provided) to enrich metadata. If a service appears in `service_inventory` but no report is found, log a warning: "Service '{name}' listed in service_inventory but no MOD report found at expected path."

### Step 2: Parse Individual MOD Reports

For each MOD report JSON found, extract the data needed for portfolio-level analysis.

#### 2.1 Service Metadata

Extract from the JSON `metadata` object at the root:

- **Service/repository name** — from `metadata.repo_name` (or derive from the filename)
- **Analysis date** — from `metadata.analysis_date` (validate YYYY-MM-DD format)
- **Repo type** — from `metadata.repo_type` (one of: `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`). If absent, assume `application`.
- **Service archetype** — from `metadata.service_archetype` when `repo_type` is `application`
- **Overall score** — from `overall_score` at the root (validate 1.0–4.0 range)
- **Category scores** — from `categories[]` entries. Each entry has `category_id` (INF/APP/DATA/SEC/OPS) and `numeric_score` (1.0–4.0 or null when all questions in the category resolved to N/A / Not Evaluated).

#### 2.2 Detailed Findings (Per-Question)

From the JSON `findings[]` array, extract for each entry:

- **Question ID** — `findings[i].question_id` (e.g., INF-Q1, APP-Q2, DATA-Q3)
- **Internal score** — `findings[i].mod_metadata.internal_score` (1, 2, or 3 — score 4 emits no finding)
- **Unified severity** — `findings[i].severity` (High / Medium / Low)
- **Score label** — `findings[i].mod_metadata.score_label` (Not Ready / Needs Work / Partial)
- **Core question flag** — `findings[i].mod_metadata.core_question` (boolean)
- **Archetype calibrated** — `findings[i].mod_metadata.archetype_calibrated` (boolean)
- **Finding description** — `findings[i].description`
- **Gap** — `findings[i].gap`
- **Recommendation** — `findings[i].recommendation`
- **Evidence** — `findings[i].evidence` ({file, lines} or null)

From the JSON `evaluations[]` array (if present), extract entries for questions that resolved to N/A, Not Evaluated (archetype-N/A), Not Evaluated (surface-gated), or passing — these do NOT appear in `findings[]`.

**N/A Handling During Parsing:**

When a question is in `evaluations[]` with status `N/A` or `Not Evaluated`:
- Record it as N/A for this service
- **Do NOT treat N/A as score 0 or score 1** — N/A means the question does not apply to the repo type or surface
- **Exclude N/A resolutions from portfolio-level category averages and overall score calculations** — they should not count in either the numerator or the denominator
- Track which questions are N/A per service for use in cross-cutting analysis (Step 5)

#### 2.3 Technology Stack

Extract technology information from the JSON `metadata.tech_stack` object and per-finding evidence:

- **Programming languages** — from `metadata.tech_stack.language` and APP-Q1 finding
- **Database engines** — from INF-Q2 and DATA finding evidence (identify managed vs self-managed)
- **Compute patterns** — from INF-Q1 finding evidence (EC2, Lambda, ECS, EKS, Fargate, containers)
- **IaC tools** — from INF-Q5 / INF-Q10 finding evidence (Terraform, CloudFormation, CDK, Helm, Kustomize)
- **CI/CD tools** — from INF-Q11 finding evidence (GitHub Actions, GitLab CI, Jenkins, CodeBuild, CodePipeline)
- **Container orchestration** — from INF-Q1 and container-related finding evidence (ECS, EKS, Docker Compose, Kubernetes)
- **Messaging/streaming** — from INF-Q4 finding evidence (SQS, SNS, EventBridge, Kafka, Kinesis, MSK)

#### 2.4 Pathway Data

From the JSON `pathways[]` array, extract for each of the 7 entries:

- **Pathway id** — `pathways[i].id` (one of `move-to-cloud-native`, `move-to-containers`, `move-to-open-source`, `move-to-managed-databases`, `move-to-managed-analytics`, `move-to-modern-devops`, `move-to-ai`)
- **Pathway name** — `pathways[i].name`
- **Status** — `pathways[i].status` (`Triggered` / `Not Triggered` / `Not Applicable`)
- **Priority** — `pathways[i].priority` (High / Medium / Low, or null)
- **Estimated effort** — `pathways[i].effort` (High / Medium / Low, or null)
- **Key trigger criteria** — `pathways[i].key_trigger_criteria`
- **Triggering questions** — `pathways[i].triggering_questions[]` with `(question_id, score, note, evidence)`
- **Not-triggered reason** — `pathways[i].not_triggered_reason` (optional prose)

#### 2.5 Error Handling

- Log warnings for missing optional fields (use defaults where possible)
- Handle duplicate service names with disambiguation using repository path
- If a report is missing required fields, exclude the report from portfolio analysis and log a warning.


### Step 3: Build Executive Dashboard

Aggregate the parsed data into a portfolio-level executive dashboard with score overview and category breakdowns.

#### 3.1 Portfolio Score Overview

Calculate portfolio-wide scores:

| Metric | Calculation |
|--------|-------------|
| Portfolio Overall Score | Arithmetic mean of all service overall scores (exclude services where overall score could not be calculated) |
| Score Range | Min and max overall scores across services |
| Score Variance | Standard deviation of overall scores — indicates portfolio consistency |

**Readiness Distribution:**
- **✅ Mature (3.5–4.0)**: Count and percentage of services
- **🟡 Partial (2.5–3.4)**: Count and percentage of services
- **🟠 Needs Work (1.5–2.4)**: Count and percentage of services
- **❌ Not Ready (<1.5)**: Count and percentage of services

#### 3.2 Category Score Averages

For each of the 5 categories, calculate the portfolio-level average:

**N/A Exclusion Rule:** When calculating portfolio-level category averages, exclude services where that category is "N/A". The portfolio category average is the arithmetic mean of only the non-N/A category scores across services.

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | X.X | X.X | X.X | N |
| Application Architecture (APP) | X.X | X.X | X.X | N |
| Data Platform (DATA) | X.X | X.X | X.X | N |
| Security Baseline (SEC) | X.X | X.X | X.X | N |
| Operations & Observability (OPS) | X.X | X.X | X.X | N |

If all services have N/A for a category, the portfolio category average is "N/A".

#### 3.3 Portfolio Summary Metrics

| Metric | Value |
|--------|-------|
| Total services assessed | Count of valid MOD reports parsed |
| Portfolio overall score | X.X / 4.0 |
| Highest scoring service | <name> (X.X) |
| Lowest scoring service | <name> (X.X) |
| Pathways triggered (portfolio-wide) | N of 7 |
| Cross-cutting Foundational Blockers | N |
| Cross-cutting Improvement Opportunities | N |

#### 3.4 Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | N | X% |
| infrastructure-only | N | X% |
| deployment-config | N | X% |
| monorepo | N | X% |
| library | N | X% |

#### 3.5 Readiness Snapshot

Produce a structured, machine-parseable summary block containing the key portfolio metrics. This block is designed for consumption by dashboard and tracking systems that build time-series views across multiple analysis runs.

The snapshot captures the state of the portfolio at analysis time. Delta calculations (score improvements, pathway resolutions, velocity) are the responsibility of the consuming system, not this TD.

Fields:

| Field | Type | Source |
|-------|------|--------|
| `analysis_date` | string (YYYY-MM-DD) | Report date |
| `total_services` | integer | Count of assessed services |
| `portfolio_score` | float | Overall portfolio score average |
| `score_range_min` | float | Lowest individual service score |
| `score_range_max` | float | Highest individual service score |
| `mature_services` | integer | Count with score >= 3.5 |
| `partial_services` | integer | Count with score 2.5–3.4 |
| `needs_work_services` | integer | Count with score 1.5–2.4 |
| `not_ready_services` | integer | Count with score < 1.5 |
| `pathways_triggered` | integer | Count of distinct pathways triggered across portfolio |
| `foundational_blockers` | integer | Count of criteria scoring < 2 in 2+ repos |
| `improvement_opportunities` | integer | Count of criteria scoring < 3 at-or-above the scaling threshold (max(3, 33% of applicable repos); floor of 2 for portfolios with fewer than 4 applicable repos) |
| `category_inf` | float or "N/A" | Infrastructure & DevOps portfolio average |
| `category_app` | float or "N/A" | Application Architecture portfolio average |
| `category_data` | float or "N/A" | Data Platform portfolio average |
| `category_sec` | float or "N/A" | Security Baseline portfolio average |
| `category_ops` | float or "N/A" | Operations & Observability portfolio average |
| `portfolio_level_avg` | float | Average score of portfolio-level questions (PORT-MOD-Q1–Q5) |

### Step 3b: Technology Stack Summary

Consolidate technology usage across the portfolio to identify standardization opportunities and diversity metrics.

#### 3b.1 Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| <language> | N | X% |

#### 3b.2 Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| <engine> | Relational / NoSQL / Vector / Cache | N | Yes / No / Mixed |

Identify:
- **Self-managed databases** — databases running on EC2 or self-managed containers
- **Managed databases** — RDS, Aurora, DynamoDB, DocumentDB, ElastiCache, etc.
- **Commercial databases** — Oracle, SQL Server, or other licensed engines
- **Open source databases** — PostgreSQL, MySQL, MariaDB, MongoDB, Redis, etc.

#### 3b.3 Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| EC2 / VM-based | N | X% |
| Containers (ECS/EKS/Fargate) | N | X% |
| Serverless (Lambda) | N | X% |
| Mixed | N | X% |

#### 3b.4 IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| <tool> | IaC / CI/CD | N |

#### 3b.5 Standardization Opportunities

Based on the technology diversity analysis:
- Identify technologies used by only 1 service (candidates for consolidation)
- Identify the dominant technology in each category (candidate for standardization)
- Calculate a technology diversity score: number of distinct technologies / number of services
- If `preferences` were provided, note alignment between current stack and preferred technologies

#### 3b.6 Blueprint Candidates — Repos as Standardization Templates

Identify specific repositories whose operational patterns (IaC, CI/CD, deployment, security pipeline) are strong enough to serve as blueprints for other repos in the portfolio. These are repos that "got it right" — their configurations can be copied, adapted, or extracted into shared templates.

**Identification criteria** — A repo qualifies as a blueprint candidate when it scores **>= 3 on at least 3** of the following operational questions:

| Question | What it demonstrates |
|---|---|
| INF-Q10 (IaC Coverage) | Well-structured IaC that can be templated |
| INF-Q11 (CI/CD Automation) | Pipeline patterns that can be reused |
| OPS-Q5 (Deployment Strategy) | Canary/blue-green configs that can be copied |
| INF-Q5 (Network Security) | VPC/SG patterns that can be standardized |
| SEC-Q7 (Security Pipeline) | SAST/scanning configs that can be shared |
| INF-Q1 (Managed Compute) | EKS/ECS/Lambda patterns that can be templated |

**Scoring algorithm:**

```
for each repo in portfolio:
    if repo.repo_type in ('library'):
        continue  # Libraries don't have infra patterns to blueprint
    
    blueprint_questions = [INF-Q10, INF-Q11, OPS-Q5, INF-Q5, SEC-Q7, INF-Q1]
    high_scores = count(repo.score[q] >= 3 for q in blueprint_questions if q is not N/A)
    
    if high_scores >= 3:
        classify as Blueprint Candidate
        record: repo name, qualifying scores, specific patterns to extract
```

**Output for each blueprint candidate:**

- **Repo name** and overall score
- **Qualifying scores** — which operational questions scored >= 3 and what patterns they demonstrate
- **Extractable patterns** — specific configurations, templates, or modules that other repos could adopt:
  - IaC modules (Terraform modules, CDK constructs, Helm charts)
  - CI/CD pipeline definitions (GitHub Actions workflows, buildspec files)
  - Deployment configurations (CodeDeploy appspec, ArgoCD configs, Helm values)
  - Security scanning configs (Dependabot, Snyk, SonarQube configs)
  - Network security patterns (VPC modules, security group templates)
- **Applicable to** — which other repos in the portfolio would benefit from adopting these patterns (repos scoring < 2 on the same questions)
- **Adoption effort** — Low (copy config), Medium (adapt to different stack), High (requires refactoring)

**Report section:**

```markdown
### 🏗️ Blueprint Candidates — Repos as Standardization Templates

> These repos demonstrate strong operational patterns that can be extracted and 
> applied across the portfolio. Use them as reference implementations when 
> modernizing other services.

| Blueprint Repo | Qualifying Scores | Extractable Patterns | Benefits For |
|---|---|---|---|
| <repo> | INF-Q10=4, INF-Q11=3, SEC-Q7=3 | Terraform modules, GitHub Actions workflows, Dependabot config | <N> repos scoring < 2 on these questions |
```

If no repos qualify as blueprint candidates, include a note:

```markdown
### 🏗️ Blueprint Candidates

No repos currently qualify as blueprint candidates (scoring >= 3 on 3+ operational questions). 
This indicates a portfolio-wide operational maturity gap — consider establishing reference 
implementations as part of Phase 0 (Cross-Cutting Foundation) in the roadmap.
```

**Integration with roadmap (Step 6):** When blueprint candidates exist, Phase 1 activities for other repos should reference the blueprint: "Adopt [blueprint-repo]'s CI/CD pipeline pattern" rather than "Create CI/CD pipeline from scratch." This reduces effort estimates and provides concrete starting points.


### Step 4: Build Service Dependency Map

Construct and analyze the service dependency graph using `dependency_overrides` from `additionalPlanContext`.

#### 4.1 Dependency Graph Construction

If `dependency_overrides` is provided:

- Create a directed graph with services as nodes and dependencies as edges
- For each dependency override entry:
  - Add an edge from `source` to `target`
  - Label the edge with `type` (sync, async, shared_db, shared_infra) and `description`
- Cross-reference with discovered services — log a warning if a dependency references a service not found in the report inventory

**Dependency Types:**

| Type | Description | Modernization Implication |
|------|-------------|--------------------------|
| `sync` | Synchronous REST/gRPC call | Tight coupling — source must be modernized after or concurrently with target |
| `async` | Message queue, event bus, pub/sub | Loose coupling — services can be modernized more independently |
| `shared_db` | Multiple services access same database | Database migration affects all consumers — coordinate carefully |
| `shared_infra` | Common API gateway, auth system, load balancer | Shared infrastructure changes affect all dependent services |

#### 4.2 Coupling Score Calculation

For each service pair with dependencies, calculate coupling level:

- **High**: Synchronous dependency + shared database, OR 3+ dependency types between the pair
- **Medium**: Synchronous dependency only, OR 2 dependency types between the pair
- **Low**: Asynchronous only, OR shared infrastructure only

#### 4.3 Graph Metrics

For each service, calculate:

- **Fan-in** — Count of services that depend on this service (number of edges pointing to it). High fan-in indicates a foundation service.
- **Fan-out** — Count of services this service depends on (number of edges pointing from it). High fan-out indicates a consumer service.
- **Blast radius** — Transitive impact calculation using breadth-first search from the service node. Expressed as a percentage of the total portfolio (number of transitively affected services / total services × 100).
- **Foundation services** — Services with fan-in >= 3 AND fan-out <= 1 (many depend on them, they depend on few)
- **Leaf services** — Services with fan-in <= 1 AND fan-out >= 2 (few depend on them, they depend on many)

#### 4.4 Circular Dependency Detection

- Use Tarjan's strongly connected components algorithm (or equivalent)
- Any strongly connected component (SCC) with size > 1 indicates a circular dependency
- Flag all circular dependencies as architectural risks requiring Phase 0 resolution
- List the services involved in each circular dependency cycle

#### 4.5 Critical Path Analysis

- Identify services that must be modernized first due to high fan-in (foundation services)
- Map dependency chains to determine sequencing constraints for the roadmap (Step 6)
- Calculate the longest dependency chain length — this determines the minimum number of sequential phases needed

#### 4.6 No Dependency Information

If `dependency_overrides` is not provided:

**Infer dependencies from individual MOD reports.** Rather than skipping dependency analysis entirely, extract dependency information from the individual report findings:

1. **Scan individual report findings** for evidence of inter-service communication:
   - Look for mentions of gRPC/REST calls to other services in the portfolio (e.g., "calls cartservice via gRPC", "synchronous dependency on productcatalogservice")
   - Look for shared data store references (e.g., "Redis backing store", "shared database")
   - Look for service names mentioned in context fields, findings, or technology stack sections
   - Look for import/client references to other services in the codebase
   - Look for infrastructure dependencies (e.g., "shared GKE cluster", "common Istio mesh")

2. **Construct an inferred dependency graph** using the same structure as explicit `dependency_overrides`:
   - Set `type` based on communication pattern: `sync` for REST/gRPC calls, `async` for message queue/event references, `shared_db` for shared data store references, `shared_infra` for shared infrastructure references
   - Set `description` from the evidence found in the report
   - Mark all inferred dependencies as `"inferred": true` to distinguish from explicit overrides

3. **Apply Steps 4.1–4.5 normally** using the inferred dependency graph — calculate coupling scores, fan-in/fan-out, blast radius, detect circular dependencies, and perform critical path analysis

4. **Add a note in the service dependency map section:**

> Dependencies were inferred from individual MOD report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

If no dependencies can be inferred from the reports, display a note that no dependency information was available and produce the roadmap using priority-based ordering only (P0 → P1 → P2) without dependency-based phase assignment.

### Step 5: Identify Cross-Cutting Concerns

Identify modernization gaps that appear across multiple services. Cross-cutting concerns are classified into two tiers based on score severity.

#### 5.1 Two-Tier Classification

**Tier 1 — 🚨 Foundational Blockers:**
- Criteria scoring **< 2** in **2 or more** repos (excluding N/A)
- These represent fundamental gaps that block all modernization efforts
- Must be addressed before service-level modernization can proceed

**Tier 2 — 💡 Improvement Opportunities:**
- Criteria scoring **< 3** in **max(3, 33% of applicable repos)** (excluding N/A)
- For portfolios with fewer than 4 applicable repos for a given question, the threshold is 2 repos (same as Tier 1 but at a higher score boundary)
- These represent important gaps that are not blocking but warrant coordinated attention
- Can be addressed in parallel with other modernization work

#### 5.2 Classification Algorithm

```
for each question_id in all_37_questions:
    scores = []
    applicable_services = []
    
    for each service in portfolio:
        score = service.findings[question_id].score
        if score == "N/A":
            continue  # Skip — N/A is not a gap
        applicable_services.append(service)
        scores.append(score)
    
    if len(scores) == 0:
        continue  # All services have N/A for this question
    
    # Check Tier 1: Foundational Blockers
    blocker_count = count(s < 2 for s in scores)
    if blocker_count >= 2:
        classify as Foundational Blocker
        record: question_id, blocker_count, applicable_services count
        continue
    
    # Check Tier 2: Improvement Opportunities
    gap_count = count(s < 3 for s in scores)
    tier2_threshold = max(3, ceil(len(applicable_services) * 0.33))
    if len(applicable_services) < 4:
        tier2_threshold = 2  # Small portfolio accommodation
    if gap_count >= tier2_threshold:
        classify as Improvement Opportunity
        record: question_id, gap_count, applicable_services count
```

**Important classification rules:**
- Evaluate tiers in order: Tier 1 → Tier 2. A criterion is classified into the first tier it matches.
- A criterion that qualifies for Tier 1 (score < 2 in 2+ repos) is classified as Tier 1 even if it also qualifies for Tier 2. Tier 1 takes precedence.
- N/A scores are excluded from all tier calculations — a service where a criterion is N/A does not count toward any tier's service count.
- This classification is based on score severity.

#### 5.3 Cross-Cutting Concern Output

For each classified concern, record:

- **Question ID** — e.g., INF-Q5
- **Question topic** — e.g., "Infrastructure as Code Coverage"
- **Tier** — Foundational Blocker or Improvement Opportunity
- **Affected services** — List of service names with scores below the threshold
- **Applicable services** — Count of services where this question is not N/A
- **Impact** — X of Y applicable services have this gap
- **Score distribution** — How scores are distributed across services for this question
- **Portfolio-level recommendation** — A coordinated recommendation addressing all affected services


### Step 5b: Infrastructure Cross-Referencing

When a portfolio contains `infrastructure-only` or `deployment-config` repos alongside `application` repos, the infra/deployment repos often provide capabilities (IaC, CI/CD, network security, deployment strategy, audit logging) that serve the application repos. Individual application repo analyses cannot see these external artifacts and may score 1 on questions whose answers live in a companion repo. This step identifies those cross-references and annotates findings accordingly.

> **Important**: This step does NOT change individual repo scores. It produces contextual annotations that inform the portfolio-level view and reduce false-positive noise in cross-cutting concern analysis.

#### 5b.1 Identify Infrastructure and Deployment Repos

From the parsed report inventory (Step 2), identify repos with `repo_type` of:
- `infrastructure-only` — Contains IaC (Terraform, CDK, CloudFormation, Helm) but no application code
- `deployment-config` — Contains CI/CD pipelines, Kubernetes manifests, GitOps configs, Ansible playbooks

If no repos of these types exist in the portfolio, skip this step entirely.

#### 5b.2 Extract Infrastructure Capabilities

For each `infrastructure-only` or `deployment-config` repo, extract the capabilities it provides by examining its scored questions:

| Capability | Source Questions | What it covers |
|---|---|---|
| **IaC Coverage** | INF-Q10 score >= 3 | Terraform/CDK/CFN modules that provision infrastructure for other repos |
| **Network Security** | INF-Q5 score >= 3 | VPC, subnets, security groups, NACLs defined in IaC |
| **CI/CD Automation** | INF-Q11 score >= 3 | Shared pipelines, deployment automation |
| **Deployment Strategy** | OPS-Q5 score >= 3 | Blue/green, canary, or rolling deployment configs |
| **Audit Logging** | SEC-Q1 score >= 3 | CloudTrail, centralized logging configuration |
| **Backup/Recovery** | INF-Q8 score >= 3 | Backup plans, retention policies, PITR |
| **Auto-Scaling** | INF-Q7 score >= 3 | ASG, HPA, scaling policies |
| **Managed Compute** | INF-Q1 score >= 3 | EKS/ECS/Fargate/Lambda provisioning |
| **Managed Databases** | INF-Q2 score >= 3 | RDS/Aurora/DynamoDB provisioning |

Record each capability with:
- The infra/deployment repo name that provides it
- The score achieved (3 or 4)
- The evidence (from the finding's evidence field)

#### 5b.3 Map Capabilities to Application Repos

For each application repo that scored 1 on a question where an infra/deployment repo scored >= 3 on the same question:

1. **Create a cross-reference annotation** on the application repo's finding:

```
Portfolio Context: [infra-repo-name] (infrastructure-only) scores [score] on [question_id] 
and likely provides this capability for [app-repo-name]. The Score 1 on [app-repo-name] 
may be a false positive — the capability exists in the portfolio but in a separate repo. 
Verify that [infra-repo-name]'s IaC/config covers [app-repo-name]'s deployment.
```

2. **Questions eligible for cross-referencing** (these are the "external context" questions that commonly live outside application repos):

| Application repo question | Cross-references with infra/deployment repo question |
|---|---|
| SEC-Q1 (Audit Logging) score = 1 | SEC-Q1 score >= 3 in any infra repo |
| INF-Q5 (Network Security) score = 1 | INF-Q5 score >= 3 in any infra repo |
| INF-Q10 (IaC Coverage) score = 1 | INF-Q10 score >= 3 in any infra repo |
| OPS-Q5 (Deployment Strategy) score = 1 | OPS-Q5 score >= 3 in any deployment-config repo |
| INF-Q1 (Managed Compute) score = 1 | INF-Q1 score >= 3 in any infra repo |
| INF-Q2 (Managed Databases) score = 1 | INF-Q2 score >= 3 in any infra repo |
| INF-Q7 (Auto-Scaling) score = 1 | INF-Q7 score >= 3 in any infra repo |
| INF-Q8 (Backup/Recovery) score = 1 | INF-Q8 score >= 3 in any infra repo |
| INF-Q11 (CI/CD Automation) score = 1 | INF-Q11 score >= 3 in any deployment-config repo |

3. **Do NOT cross-reference** questions that are inherently per-repo (code-level concerns):
   - APP-Q1 through APP-Q6 (application architecture is per-repo)
   - DATA-Q1 through DATA-Q4 (data access patterns are per-repo)
   - SEC-Q3 through SEC-Q7 (auth, secrets, scanning are per-repo)
   - OPS-Q1 (tracing instrumentation is per-repo)
   - OPS-Q6 (integration tests are per-repo)

#### 5b.4 Adjust Cross-Cutting Concern Severity

When Step 5 classifies a question as a Foundational Blocker or Improvement Opportunity, and Step 5b identifies that an infra/deployment repo provides the capability:

- **Add a portfolio annotation** to the cross-cutting concern:

```
⚠️ Portfolio mitigation detected: [infra-repo-name] (infrastructure-only) scores [score] 
on this question, indicating the capability exists in the portfolio. [N] of [M] affected 
application repos may be covered by this shared infrastructure. Verify coverage before 
treating this as a true portfolio-wide gap.
```

- **Do NOT remove the cross-cutting concern** — it remains classified at its tier. The annotation provides context for human reviewers to validate.
- **Do NOT change individual scores** — per Step 10.2 rules.

#### 5b.5 Output

Record the cross-referencing results in the portfolio report under a dedicated subsection within Cross-Cutting Concerns:

```markdown
### 🔗 Infrastructure Cross-References

> The following application repo findings may be mitigated by capabilities in 
> infrastructure-only or deployment-config repos in this portfolio. Individual 
> scores are unchanged — verify that the infra repo's configuration covers the 
> application repo's deployment.

| App Repo | Question | Score | Potentially Covered By | Infra Score | Status |
|----------|----------|-------|------------------------|-------------|--------|
| <app-repo> | <question_id> | 1 | <infra-repo> | <3 or 4> | Verify |
```

If no infrastructure-only or deployment-config repos exist in the portfolio, omit this subsection entirely.


### Step 6: Generate Dependency-Aware Phased Roadmap

Create a four-phase roadmap with dependency-aware sequencing.

#### 6.1 Fixed Phase Names

| Phase | Name | Timeline |
|-------|------|----------|
| 0 | Cross-Cutting Foundation | Mo 0–1 |
| 1 | Quick Wins | Mo 1–2 |
| 2 | Foundation | Mo 2–4 |
| 3 | Advanced | Mo 4–6+ |

These phase names are fixed.

#### 6.2 Phase Assignment Algorithm

**Phase 0 — Cross-Cutting Foundation (Mo 0–1):**
- Cross-cutting concerns identified in Step 5 (Foundational Blockers and Improvement Opportunities)
- Shared infrastructure improvements benefiting multiple services
- Circular dependency breaking activities (must be resolved first — from Step 4.4)
- Organizational enablers (training, tooling, standards)

**Phase 1 — Quick Wins (Mo 1–2):**
- Foundation services (fan-in >= 3, fan-out <= 1) — must go first because many services depend on them
- Services with no dependencies (can start immediately)
- Services with overall score < 2.0 AND high blast radius (critical risks that affect the portfolio)
- Establish patterns and reference implementations

**Phase 2 — Foundation (Mo 2–4):**
- Services depending only on Phase 1 services (their dependencies are being addressed first)
- Services with moderate dependencies (2–3 dependencies)
- Services with overall score 2.0–3.0 (moderate gaps)
- Replicate proven patterns from Phase 1

**Phase 3 — Advanced (Mo 4–6+):**
- Leaf services (fan-in <= 1, fan-out >= 2)
- Services with overall score >= 3.0 (minor gaps only)
- Optional enhancements and advanced capabilities
- Continuous improvement and optimization

#### 6.3 Service Ordering Within Phases

Within each phase, order services by:
1. **Priority** — P0 first, then P1, then P2 (from `service_inventory` or report metadata)
2. **Dependency ordering** — Services with higher fan-in before services with lower fan-in (more critical services first)
3. **Score** — Lower-scoring services before higher-scoring services (more work needed = start earlier)

If priority is not set for a service, treat it as P2 (lowest priority).

#### 6.4 Sequencing Validation

After assigning services to phases:
- Verify no service is assigned to a phase earlier than any of its dependencies
- Verify all services are assigned to exactly one phase
- Flag any sequencing violations for manual review
- If a circular dependency exists and was not broken in Phase 0, log a warning

#### 6.5 Per-Service Assignment

For each service in the roadmap, include:

- **Service name** and **priority** (P0/P1/P2)
- **Current overall score** and **target state**
- **Key activities** required (derived from the service's top gaps)
- **Dependencies** — services that must complete first (from dependency graph)
- **Blocks** — services waiting on this one (from dependency graph)
- **Estimated effort** — High / Medium / Low (derived from the gap between current score and target)

#### 6.6 Roadmap Without Dependency Information

If `dependency_overrides` was not provided:
- Assign services to phases based on priority and score only:
  - Phase 1: P0 services and services with score < 2.0
  - Phase 2: P1 services and services with score 2.0–3.0
  - Phase 3: P2 services and services with score >= 3.0
- Phase 0 still contains cross-cutting concerns from Step 5
- Note in the roadmap that dependency-based ordering is not available and recommend providing `dependency_overrides` for a more accurate roadmap

#### 6.7 Target State Architecture

After generating the phased roadmap, produce a brief "Target State" summary that describes what the portfolio looks like after roadmap completion. This gives architects the destination picture, not just the gap list.

**Derive from:**
- `preferences` (prefer/avoid arrays define the desired technology stack)
- Triggered pathways (each pathway implies a target state — e.g., "Move to Containers" → "all compute on EKS/ECS")
- Cross-cutting Foundational Blockers (each resolved blocker implies a capability — e.g., "IaC coverage" → "all infrastructure defined in Terraform")
- Blueprint candidates (strongest repo patterns become the standard)

**Output structure:**
- **Compute:** Target compute platform (derived from Move to Containers pathway + preferences)
- **Data:** Target database/storage platform (derived from Move to Managed Databases + Move to Open Source pathways)
- **Observability:** Target observability stack (derived from PORT-MOD-Q2 + OPS category gaps)
- **CI/CD:** Target pipeline pattern (derived from Move to Modern DevOps pathway + blueprint candidates)
- **Security:** Target security posture (derived from SEC category + PORT-MOD-Q5)

Each entry should be 1-2 sentences stating the target state, not the remediation steps (those are in the roadmap). Example: "Compute: All services containerized on EKS with Karpenter autoscaling. No EC2 instances in production." When `preferences` are not provided, derive targets from triggered pathways and AWS best practices only.

### Step 7: Aggregate Pathways Across Portfolio

Aggregate individual service pathway triggers to produce a portfolio-level modernization pathway plan.

#### 7.1 Portfolio Pathway Aggregation

For each of the 7 AWS Modernization Pathways:
- Count the number of services where the pathway status is "Triggered"
- Count the number of services where the pathway status is "Not Triggered"
- Count the number of services where the pathway status is "Not Applicable"
- Calculate the percentage of portfolio where the pathway is triggered (triggered / total services × 100)
- Determine portfolio-level priority:
  - **High**: Pathway triggered for >= 60% of services OR triggered for any P0 foundation service
  - **Medium**: Pathway triggered for 30–59% of services
  - **Low**: Pathway triggered for < 30% of services
- Aggregate estimated effort level across all affected services

**Move to AI — Not Triggered Reason Distinction:**

For the Move to AI pathway specifically, distinguish between two reasons a service may have status "Not Triggered":

1. **Contextual guard suppression** — The service had no AI/agent/LLM intent in its context, so the pathway was correctly suppressed by the contextual guard. The Not Triggered reason will contain "No AI/agent intent detected in portfolio or service context."
2. **Already present** — AI frameworks were already detected in the service, so the pathway did not need to trigger.

When aggregating Move to AI, count the services in each Not Triggered sub-category separately:
- `X` = number of services where Move to AI is Triggered
- `Y` = total number of assessed services
- `Z` = number of services where Move to AI was Not Triggered due to contextual guard suppression (no AI intent in context)

Report the Move to AI aggregation as:

```
Move to AI: Triggered in X of Y services (Z services had no AI intent in context — pathway correctly suppressed)
```

This distinction appears in the pathway detail narrative for Move to AI, not in the repo-level aggregation table structure (Step 7.2). The table continues to show each repo in exactly one column (Triggered, Not Triggered, or Not Applicable).

#### 7.2 Portfolio Pathway Aggregation Table

Produce a repo-level aggregation table showing exactly which repositories fall into each pathway status:

```markdown
| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | <comma-separated repo names or "—"> | <comma-separated repo names or "—"> | <comma-separated repo names or "—"> |
| Move to Containers | ... | ... | ... |
| Move to Open Source | ... | ... | ... |
| Move to Managed Databases | ... | ... | ... |
| Move to Managed Analytics | ... | ... | ... |
| Move to Modern DevOps | ... | ... | ... |
| Move to AI | ... | ... | ... |
```

**Rules:**
- Every assessed repo MUST appear in exactly ONE column per pathway row. No repo may be missing from a row, and no repo may appear in more than one column per row.
- If a column has no repos for a given pathway, display "—" instead of leaving it blank.
- All 7 pathways MUST have a row in the table, even if no repos trigger that pathway.

**Validation:**
- After constructing the table, verify that for each pathway row, the total count of repos across the three columns (Triggered + Not Triggered + Not Applicable) equals the total number of assessed repos. If any repo is missing or duplicated, log a warning and correct the table.

#### 7.3 Cross-Pathway Dependencies

Identify dependencies between pathways at the portfolio level:
- Move to Containers is often a prerequisite for Move to Cloud Native (containerize before decomposing)
- Move to Open Source may be a prerequisite for Move to Managed Databases (migrate off proprietary first)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is a prerequisite for Move to AI in many cases (data foundations needed)

#### 7.4 Pathway-to-Phase Mapping

Map pathway execution to the 4-phase roadmap:
- **Phase 0**: Move to Modern DevOps (enables all other pathways)
- **Phase 1**: Move to Containers, Move to Open Source (foundational changes)
- **Phase 2**: Move to Cloud Native, Move to Managed Databases (build on Phase 1)
- **Phase 3**: Move to Managed Analytics, Move to AI (advanced capabilities)

This mapping is indicative — actual phase assignment depends on the service-level dependency analysis in Step 6.

#### 7.5 Pathway Overlap Density

For each service, count the number of triggered pathways. Services triggering 4 or more pathways represent concentrated modernization debt requiring dedicated investment — they cannot be modernized incrementally alongside other work.

**Algorithm:**
```
for each service in portfolio:
    triggered_count = count(pathway.status == "Triggered" for pathway in service.pathways)
    service.pathway_load = triggered_count

heavy_modernization_candidates = [s for s in portfolio if s.pathway_load >= 4]
```

**Output:** Include a "Heavy Modernization Candidates" callout in the report when `heavy_modernization_candidates` is non-empty:
- List each service with pathway_load ≥ 4, showing which pathways are triggered
- Flag these as requiring dedicated sprint capacity or a focused modernization initiative
- Cross-reference with the risk register (these services likely appear as high-risk dependencies)

### Step 8: Integration Opportunities, Risk Analysis, and Resource Allocation

#### 8.1 Integration Opportunities

Identify specific opportunities for cross-service improvements:

**Shared Service Extraction:**
- Search findings for functionality mentioned in 3+ services
- Common candidates: authentication, logging, caching, notification, file processing
- For each opportunity:
  - List affected services
  - Describe current state (duplicated implementation)
  - Propose shared service solution (steered by `preferences` if provided)
  - List benefits (reduced duplication, consistency, faster development)
  - Classify implementation effort as High / Medium / Low
  - Assign priority based on impact and number of services affected

**Event-Driven Architecture Opportunities:**
- Identify services with synchronous dependencies (APP-Q3 score < 3 or sync dependencies in the dependency graph)
- Check if message queues exist in portfolio (INF-Q4 score >= 3 in any service)
- For each opportunity:
  - Describe current synchronous integration
  - Propose event-driven solution (EventBridge, SNS/SQS, MSK — steered by `preferences`)
  - List benefits (decoupling, resilience, scalability)
  - Classify effort as High / Medium / Low

**API Gateway Consolidation:**
- Identify services with separate API gateways (INF-Q3 findings)
- Propose unified API gateway strategy
- Benefits: consistent auth, rate limiting, monitoring, cost reduction

**Observability Unification:**
- Identify services with different observability stacks (OPS-Q1, OPS-Q2 findings)
- Propose unified observability platform
- Benefits: end-to-end tracing, consistent metrics, reduced tool sprawl

#### 8.2 Risk Analysis

Perform comprehensive risk analysis across the portfolio:

**High-Risk Dependency Identification:**
- Identify services with overall score < 2.0 AND fan-in >= 3 (many services depend on them)
- These are critical services in poor condition that pose portfolio-wide risk
- Calculate likelihood based on service score:
  - **High**: score < 2.0
  - **Medium**: score 2.0–3.0
  - **Low**: score >= 3.0
- Calculate impact based on blast radius:
  - **High**: blast radius >= 50%
  - **Medium**: blast radius 25–50%
  - **Low**: blast radius < 25%

**Single Points of Failure (SPOF):**
- Identify services with blast radius >= 50% of portfolio
- Check findings for redundancy mentions (HA, multi-AZ, failover)
- If no redundancy mentioned AND high blast radius, flag as SPOF

**Circular Dependency Risks:**
- All circular dependencies detected in Step 4.4 are architectural risks
- Circular dependencies prevent independent deployment and scaling
- Must be broken in Phase 0 before service-level modernization

**Data Availability Risks:**
- Identify services with self-managed databases (INF-Q2 score < 3) AND high fan-in
- Self-managed databases are harder to scale and maintain
- When many services depend on them, availability risk is amplified

**Observability Blind Spots:**
- Identify services without distributed tracing (OPS-Q1 score < 3) AND high fan-out
- Services that call many others need tracing to debug issues

**Risk Matrix:**

Generate a likelihood × impact matrix:

| | High Impact | Medium Impact | Low Impact |
|---|---|---|---|
| **High Likelihood** | 🔴 Critical | 🟠 High | 🟡 Medium |
| **Medium Likelihood** | 🟠 High | 🟡 Medium | 🟢 Low |
| **Low Likelihood** | 🟡 Medium | 🟢 Low | 🟢 Low |

For each identified risk:
- Assign likelihood and impact
- Determine priority from the matrix
- Generate specific mitigation recommendation
- Include mitigation effort level and recommended phase

#### 8.3 Resource Allocation Recommendations

**Team Structure Recommendation:**
- IF cross-cutting concerns count >= 5, THEN recommend centralized platform team
- IF cross-cutting concerns count < 5, THEN recommend federated model with embedded platform engineers

**Skill Gap Analysis:**
- Extract required skills from roadmap activities (e.g., "containerize application" requires Docker/ECS/EKS skills)
- Extract current skills from analysis findings (e.g., "team has experience with Lambda")
- Compare required vs current to identify gaps
- Common gaps: IaC (Terraform/CDK), containers (Docker/ECS/EKS), observability (X-Ray/CloudWatch), database migration (DMS)

**Training Recommendations:**
- For each skill gap, recommend specific AWS Skill Builder courses or workshops
- Prioritize training for Phase 0 and Phase 1 skills (needed first)

**External Support Recommendations:**
- Recommend AWS Professional Services or consulting partners for:
  - High-risk activities (e.g., database migration, architecture redesign)
  - Skill gaps that cannot be filled internally in time
  - Accelerating Phase 0 shared infrastructure work

### Step 9: Generate AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.** AWS programs are engagement-level decisions scoped to the customer's overall estate, not per-repo. The portfolio view has the right scope to make these recommendations.

Based on the portfolio-wide analysis findings from previous steps, evaluate eligible AWS engagement programs against their trigger conditions using the shared **AWS Program & GTM Library** (`references/program-library.md`, shipped alongside this definition) — the single authoritative catalog. Include a program only if its trigger condition is met. If no programs are triggered, include a brief note instead.

#### 9.1 Programs Catalog and Trigger Logic

Load the shared **AWS Program & GTM Library** (`references/program-library.md`) and evaluate **every `[MOD]` and `[ARA+MOD]` program** against the portfolio findings, applying each program's signal patterns, "DO NOT recommend when" exclusions, and qualification criteria. Include a program only if its signal patterns match AND none of its exclusions apply. Multiple programs can be triggered simultaneously. Follow the library's prioritization, `Funded Programs → Engagement Models` grouping, status filtering, assessment-overlap / EBA-vs-AML rules, and run its reasoning checklist before finalizing. Cap the final list at 3–5, and never expose the internal 1–4 maturity score — use severity/classification language only.

#### 9.2 Program Recommendations Output

For each triggered program:

- **Program name and acronym**
- **Relevance** — Why this program is recommended based on portfolio findings
- **Trigger findings** — Specific portfolio metrics that triggered the recommendation (e.g., "4 of 6 services have overall score < 2.5")
- **What it provides** — Brief description of the program's value
- **Next step** — Recommended action (e.g., "Request MAP engagement via AWS Solutions Architect")

If no programs are triggered, include: "No specific AWS program recommendations based on current findings. As the portfolio evolves, re-assess to identify program eligibility."


### Step 10: Evaluate Portfolio-Level Questions

Evaluate questions that can only be answered by looking across multiple repos. These are distinct from cross-cutting analysis (Step 5) which aggregates individual scores — portfolio-level questions assess capabilities that no individual repo analysis can see.

Individual report scores are never overridden. Where a portfolio-level finding provides context for individual gaps, annotate with "potentially mitigated — verify" but do not change individual scores.

#### 10.1 Portfolio-Level Questions (5)

| ID | Question | Score Rubric | How to Evaluate |
|----|----------|-------------|-----------------|
| PORT-MOD-Q1 | **IaC Standardization** — Are services using a consistent IaC tool across the portfolio? | 4: Single IaC tool across all services. 3: Primary tool covers 80%+, minor exceptions. 2: 2-3 different tools with no standard. 1: No IaC or completely fragmented. | Count distinct IaC tools across repos (Terraform, CDK, CloudFormation, Pulumi, none). Calculate the percentage covered by the most common tool. Factor in the portfolio's preferred IaC tool from preferences. |
| PORT-MOD-Q2 | **Shared Observability Platform** — Is there a centralized observability stack (tracing, logging, metrics) spanning all services? | 4: Centralized tracing + logging + metrics with cross-service correlation. 3: Centralized logging and metrics but no cross-service tracing. 2: Some shared tooling but inconsistent adoption. 1: Each service has independent or no observability. | Check for: shared CloudWatch Log Groups, shared X-Ray/ADOT configuration, shared dashboards, consistent metric namespaces. Cross-reference with individual OPS-Q1 (tracing), OPS-Q2 (SLOs), OPS-Q3 (metrics) scores. |
| PORT-MOD-Q3 | **Dependency Cycle Health** — Are there circular dependencies that block independent modernization? | 4: No circular dependencies. 3: Circular deps exist but are async-only (breakable). 2: Sync circular deps exist with known resolution path. 1: Sync circular deps with no resolution path, blocking modernization. | Using the dependency graph from Step 4, detect cycles. Classify each cycle by dependency type (sync vs async). Sync cycles are harder to break. Score based on severity and resolution feasibility. |
| PORT-MOD-Q4 | **Technology Diversity** — How fragmented is the technology stack across the portfolio, distinguishing intentional polyglot from accidental sprawl? | 4: Low diversity (1-2 languages, 1 IaC tool, 1 DB engine) OR intentional polyglot where each language maps consistently to a service archetype (e.g., Go for networking, Python for ML, TypeScript for frontends). 3: Moderate diversity (2-3 languages, 1-2 IaC tools) with mostly consistent patterns. 2: High diversity (4+ languages, 3+ IaC tools, mixed DB engines) with no consistent mapping to service roles — accidental sprawl. 1: Extreme fragmentation with no standardization effort and no archetype justification. | Calculate technology diversity score: count distinct languages, IaC tools, DB engines, compute patterns, CI/CD tools. Divide by number of services. **Intentional polyglot adjustment:** if each language maps consistently to a specific archetype or domain (verifiable from service_inventory tags and archetypes), do not penalize — score based on consistency rather than raw count. Factor in preference alignment. |
| PORT-MOD-Q5 | **Shared Security Posture** — Is there a centralized security scanning pipeline, shared WAF, or unified vulnerability management across the portfolio? | 4: Centralized security scanning + shared WAF + unified vuln management. 3: Shared WAF or centralized scanning but not both. 2: Some shared security tooling but inconsistent. 1: Each service manages security independently or not at all. | Check for: shared WAF WebACL, centralized security scanning in CI/CD, shared Secrets Manager configuration, consistent IAM patterns. Cross-reference with individual SEC-Q1 through SEC-Q6 scores. |

#### 10.2 Contextual Annotations

When a portfolio-level finding provides context for individual cross-cutting concerns, add an annotation:

```markdown
> **Portfolio Context**: <portfolio-level question ID> found that <finding>.
> This may affect the severity of this concern for <services> — **verify** that <specific check>.
```

Do NOT change individual scores or cross-cutting concern classifications based on portfolio-level findings.

#### 10.3 Portfolio-Level Findings Output

Record portfolio-level question results in a dedicated section of the report. Include:

- **Question ID and topic**
- **Score** (1-4)
- **Finding** — what was observed across the portfolio
- **Evidence** — specific repos, files, or configurations
- **Recommendation** — portfolio-level action
- **Contextual Annotations** — any individual concerns this finding provides context for

Portfolio-level scores are included in the readiness snapshot but NOT in the portfolio overall score average (they are a separate dimension).



## Reference Files

This definition is split into a lean orchestration spine (this file) plus reference files, loaded on demand at the point in the flow where each is needed. Load each file when the step below directs you to — do not skip any.

- **`references/program-library.md`** — the shared, authoritative AWS Program & GTM Library. Loaded in Step 9 to recommend AWS engagement programs. This file is shipped identically alongside the portfolio-ara TD.
- **`references/01-report-template.md`** — the markdown report structure: executive dashboard, technology stack summary, dependency map, cross-cutting concerns, phased roadmap, pathway aggregation, integration opportunities, risk analysis, resource allocation, AWS programs, learning materials, service-by-service summary, analysis inventory.
- **`references/02-output-contract.md`** — the machine-readable four-artifact contract: JSON contract, top-level JSON keys, pathways aggregation, remediation roadmap, recommended actions, MD-retained execution-roadmap content, HTML visual contract, and error handling.


## Report Template

After completing the analysis steps, compile the aggregated findings into the four-artifact bundle. The full markdown report structure is in **`references/01-report-template.md`** — load that file and follow it exactly. The JSON and HTML artifacts render subsets of the same data per the Output Contract.

## Constraints and Guardrails

Strictly follow these rules at all times:

- **Read-only analysis**: Do not modify any source code, configuration, or infrastructure. Only create the output portfolio artifact bundle (MD, JSON, HTML, and metadata.json).
- **Stay on the current branch**: This is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out and perform all work there.
- **Minimum 2 reports**: The portfolio analysis requires at least 2 valid MOD reports. Terminate with a clear error if fewer than 2 are found.
- **N/A exclusion**: Scores of N/A are excluded from portfolio-level category averages (both numerator and denominator), overall score calculations, and cross-cutting concern analysis. A question that is N/A for a service does not count as a gap for that service.
- **Two-tier classification only**: Cross-cutting concerns use exactly two tiers — Foundational Blockers (score < 2 in 2+ repos) and Improvement Opportunities (score < 3 at-or-above the scaling threshold, max(3, 33% of applicable repos) with a floor of 2 for portfolios with fewer than 4 applicable repos).
- **Fixed phase names**: Roadmap phases are always named Cross-Cutting Foundation, Quick Wins, Foundation, and Advanced.
- **Dependency-aware ordering**: When dependency information is available, services must not be assigned to a phase earlier than their dependencies. Foundation services (high fan-in) go in Phase 1 or earlier. Within phases, order by priority (P0 → P1 → P2).
- **Preferences for framing only**: Technology preferences (prefer/avoid) influence recommendation language and technology suggestions. They do NOT change scores, N/A mappings, pathway trigger logic, or cross-cutting concern classification.
- **Evidence-based**: All cross-cutting findings must reference specific question IDs and service names. Do not make vague claims — state which services are affected and which questions triggered the finding.
- **All 7 pathways in aggregation**: The pathway aggregation table must include all 7 pathways, even if none are triggered. Every assessed repo must appear in exactly one column per pathway row.
- **Report completeness**: The output report must contain all required sections: executive dashboard, technology stack summary, service dependency map, cross-cutting concerns, phased roadmap, pathway aggregation, integration opportunities, risk analysis, resource allocation, AWS programs, learning materials, service-by-service summary, and analysis inventory.

## Output Contract

Emit the four-artifact bundle exactly as specified in **`references/02-output-contract.md`**: the JSON contract, top-level JSON keys, pathways aggregation, remediation roadmap, recommended actions, MD-retained execution-roadmap content, HTML visual contract, and error handling. Load that file and conform to it — it is the machine-readable contract the webapp and portfolio aggregator consume.
