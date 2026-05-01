## Name

Portfolio Modernization Assessment

## Objective

Aggregate individual repository Modernization Assessment (MOD) reports into a portfolio-level analysis that identifies cross-cutting modernization gaps, constructs service dependency graphs with coupling analysis, generates dependency-aware phased roadmaps, aggregates pathway triggers, assesses portfolio-wide risk, and provides resource allocation and AWS program recommendations — enabling coordinated modernization planning across the entire service estate.

## Summary

This transformation consumes multiple individual MOD reports (`*-mod-report.md` files) from different repositories and produces a comprehensive portfolio-level modernization view. It performs intelligent discovery and parsing of MOD reports, calculates portfolio-wide score averages and category breakdowns, summarizes the technology stack across the portfolio, constructs a service dependency graph with coupling scores and blast radius analysis, identifies two-tier cross-cutting concerns (Foundational Blockers and Improvement Opportunities), generates a dependency-aware four-phase roadmap, aggregates pathway triggers across services, identifies integration opportunities, performs risk assessment with a likelihood-impact matrix, provides resource allocation recommendations, recommends AWS engagement programs, curates learning materials, and produces a service-by-service summary.

The transformation follows a 10-step pipeline:
1. **Read Context**: Parse additionalPlanContext for portfolio framing, preferences, and dependency information
2. **Discovery**: Locate all MOD report files in the directory structure
3. **Parsing**: Extract scores, pathway data, findings, and technology stack from each report
4. **Executive Dashboard**: Build portfolio score overview and category averages
5. **Technology Stack Summary**: Consolidate technology usage across the portfolio
6. **Service Dependency Map**: Construct dependency graph with coupling scores, fan-in/fan-out, blast radius, and circular dependency detection
7. **Cross-Cutting Concerns**: Identify two-tier cross-cutting gaps (Foundational Blockers and Improvement Opportunities)
8. **Dependency-Aware Phased Roadmap**: Generate 4-phase roadmap with dependency-based service ordering
9. **Pathway Aggregation**: Aggregate pathway triggers across the portfolio
10. **Synthesis**: Integration opportunities, risk assessment, resource allocation, AWS programs, learning materials

The output is a detailed Markdown report saved as `portfolio-mod-report.md` containing:
- Executive dashboard with portfolio score overview and category averages
- Technology stack summary
- Service dependency map with coupling scores, fan-in/fan-out, blast radius, circular dependencies
- Two-tier cross-cutting concerns (Foundational Blockers, Improvement Opportunities)
- Dependency-aware phased roadmap (4 fixed phases)
- Pathway aggregation across the portfolio
- Integration opportunities
- Risk assessment with likelihood-impact matrix
- Resource allocation recommendations
- AWS Programs & Engagement Recommendations (MAP, OLA, MMP, VMP, WAMP, EBA, ISV WMP)
- Learning materials mapped to portfolio skill gaps
- Service-by-service summary

This portfolio TD focuses on cross-cutting modernization concerns, dependency-aware roadmaps, and pathway aggregation. It does not include ARA readiness profiles, agent scope evaluation, or Quick Agent Wins aggregation.

## Entry Criteria

- At least 2 individual MOD reports exist in repository directories
- MOD reports follow the expected structure: overall and category scores, pathway summary table, detailed findings for 37 questions
- Reports are accessible at specified paths or in a common directory structure
- Write permissions exist to create the output directory and portfolio report file

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning discovery, read the portfolio assessment context from `additionalPlanContext` to extract framing information, technology preferences, and service configuration.

#### 0.1 Read Portfolio Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
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

Record the resolved values from Steps 0.1–0.2 in the assessment context. They will be used in subsequent steps as follows:

- **`context`** → Used throughout the report to frame findings, recommendations, and roadmap guidance with portfolio-specific context. For example, if context mentions "legacy PHP e-commerce", recommendations reference the specific technology stack and business domain.
- **`preferences`** → Used throughout the report to steer technology recommendations. When `prefer` contains values, recommendations favor those technologies where applicable (e.g., if `prefer: ["eks"]`, container recommendations reference EKS over ECS). When `avoid` contains values, recommendations steer away from those technologies (e.g., if `avoid: ["serverless"]`, recommendations do not suggest Lambda-based approaches). Preferences influence recommendation framing only — they do not change scores, N/A mappings, or pathway trigger logic.
- **`service_inventory`** → Used to enrich service metadata (priority, repo_type, tags, service_archetype) and cross-reference with discovered reports. When a service entry includes `service_archetype`, that value is passed through to the per-service MOD TD invocation for scoring calibration on architecture-sensitive questions. When absent, each service MOD TD auto-detects its own archetype.
- **`dependency_overrides`** → Used in Step 4 to construct the service dependency graph, and in Step 6 to generate the dependency-aware phased roadmap.


### Step 1: Discovery — Locate MOD Reports

Scan the target directory structure to find all individual MOD reports.

#### 1.1 Discovery Process

- Recursively search for files matching the pattern `*-mod-report.md` in the directory tree
- For each report found, extract the project/service name from the filename (the prefix before `-mod-report.md`)
- Extract the repository path (parent directory or grandparent directory of the report file)
- Create an inventory of all services assessed with their report file locations
- Validate minimum requirement: at least 2 reports must be discovered

**Input Options:**
- A parent directory containing multiple repository folders, each with a MOD report, OR
- A list of explicit paths to MOD report files (from `service_inventory` paths)

#### 1.2 Validation

- Verify each discovered file exists and is readable
- Verify each file follows the expected MOD report structure:
  - Contains an overall score and category score table
  - Contains a pathway summary table with all 7 pathways
  - Contains detailed findings with question IDs (INF-Q1 through OPS-Q9)
- Exclude files that don't match the expected MOD report structure — log a warning for each excluded file
- Log warnings for inaccessible or malformed files
- **Terminate with a clear error if fewer than 2 valid MOD reports are found**

#### 1.3 Build Report Inventory

After discovery, compile a structured inventory:

| Field | Source |
|-------|--------|
| Service name | Extracted from filename prefix |
| Report file path | Full path to the `*-mod-report.md` file |
| Repository path | Parent directory of the report |
| Priority | From `service_inventory` if available, otherwise not set |
| Repo type | Extracted from report metadata header |
| Tags | From `service_inventory` if available, otherwise not set |

Cross-reference discovered reports with `service_inventory` (if provided) to enrich metadata. If a service appears in `service_inventory` but no report is found, log a warning: "Service '{name}' listed in service_inventory but no MOD report found at expected path."

### Step 2: Parse Individual MOD Reports

For each MOD report found, extract the data needed for portfolio-level analysis.

#### 2.1 Service Metadata

Extract from the report metadata header:

- **Service/repository name** — from the report header or filename
- **Assessment date** — from the report metadata (validate YYYY-MM-DD format)
- **Repo type** — from the metadata line `**Repository Type**: <value>` (e.g., `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`). If absent, assume `application`.
- **Overall score** — from the score table (validate 1.0–4.0 range)
- **Category scores** — for all 5 categories: Infrastructure & DevOps (INF), Application Architecture (APP), Data Platform (DATA), Security Baseline (SEC), Operations & Observability (OPS). Each is a numeric value 1.0–4.0 or "N/A".

#### 2.2 Detailed Findings (Per-Question)

For each of the 37 questions (INF-Q1 through OPS-Q9), extract:

- **Question ID** — e.g., INF-Q1, APP-Q2, DATA-Q3
- **Score** — 1, 2, 3, 4, or N/A
- **Finding** — What was observed
- **Gap** — What is missing (or N/A)
- **Recommendation** — What to do (or N/A)

**N/A Handling During Parsing:**

When a question has score N/A:
- Record it as N/A in the parsed data
- **Do NOT treat N/A as score 0 or score 1** — N/A means the question does not apply to the repo type
- **Exclude N/A scores from portfolio-level category averages and overall score calculations** — they should not count in either the numerator or the denominator
- Track which questions are N/A per service for use in cross-cutting analysis (Step 5)

#### 2.3 Technology Stack

Extract technology information from the report findings:

- **Programming languages** — from APP-Q1 findings or metadata
- **Database engines** — from INF-Q2 and DATA findings (identify managed vs self-managed)
- **Compute patterns** — from INF-Q1 findings (EC2, Lambda, ECS, EKS, Fargate, containers)
- **IaC tools** — from INF-Q5 findings (Terraform, CloudFormation, CDK, Helm, Kustomize)
- **CI/CD tools** — from INF-Q6 findings (GitHub Actions, GitLab CI, Jenkins, CodeBuild, CodePipeline)
- **Container orchestration** — from INF-Q1 and container-related findings (ECS, EKS, Docker Compose, Kubernetes)
- **Messaging/streaming** — from INF-Q4 findings (SQS, SNS, EventBridge, Kafka, Kinesis, MSK)

#### 2.4 Pathway Data

Extract pathway information from the individual report's pathway summary table:

```
| Pathway | Status | Priority | Key Trigger Criteria | Est. Effort |
```

For each pathway row, extract:
- **Pathway name** — One of the 7 AWS Modernization Pathways
- **Status** — One of: `Triggered`, `Not Triggered`, or `Not Applicable`
- **Priority** — `High`, `Medium`, `Low`, or `—` (for Not Triggered / Not Applicable)
- **Key Trigger Criteria** — Specific criteria scores that triggered the pathway, or "—", or the N/A reason
- **Est. Effort** — `High`, `Medium`, `Low`, or `—`

#### 2.5 Error Handling

- Log warnings for missing sections (use defaults where possible)
- Log warnings for malformed scores (exclude from aggregations)
- Handle duplicate service names with disambiguation using repository path
- If a report is missing the score table, attempt to derive scores from detailed findings. If findings are also missing, exclude the report from portfolio analysis and log a warning.
- If a pathway table uses an unrecognized format, log a warning and attempt best-effort parsing


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

Produce a structured, machine-parseable summary block containing the key portfolio metrics. This block is designed for consumption by dashboard and tracking systems that build time-series views across multiple assessment runs.

The snapshot captures the state of the portfolio at assessment time. Delta calculations (score improvements, pathway resolutions, velocity) are the responsibility of the consuming system, not this TD.

Fields:

| Field | Type | Source |
|-------|------|--------|
| `assessment_date` | string (YYYY-MM-DD) | Report date |
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
| `improvement_opportunities` | integer | Count of criteria scoring < 3 in 3+ repos |
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

If no dependencies can be inferred from the reports, fall back to the current behavior: display a note that no dependency information was available and produce the roadmap using priority-based ordering only (P0 → P1 → P2) without dependency-based phase assignment.

### Step 5: Identify Cross-Cutting Concerns

Identify modernization gaps that appear across multiple services. Cross-cutting concerns are classified into two tiers based on score severity.

#### 5.1 Two-Tier Classification

**Tier 1 — 🚨 Foundational Blockers:**
- Criteria scoring **< 2** in **2 or more** repos (excluding N/A)
- These represent fundamental gaps that block all modernization efforts
- Must be addressed before service-level modernization can proceed

**Tier 2 — 💡 Improvement Opportunities:**
- Criteria scoring **< 3** in **3 or more** repos (excluding N/A)
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
    if gap_count >= 3:
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
- Cross-cutting concerns affecting 3+ services (portfolio-level solutions from Step 5)
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


### Step 8: Integration Opportunities, Risk Assessment, and Resource Allocation

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

#### 8.2 Risk Assessment

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
- Extract current skills from assessment findings (e.g., "team has experience with Lambda")
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

Based on the portfolio-wide assessment findings from previous steps, evaluate each of the 8 AWS engagement programs below against its trigger condition. Include a program in the recommendations only if its trigger condition is met. If no programs are triggered, include a brief note instead.

#### 9.1 Programs Catalog and Trigger Logic

| Program | Acronym | Trigger Condition | How to Evaluate |
|---------|---------|-------------------|-----------------|
| Migration Acceleration Program | MAP | Portfolio has 3+ repos with overall score < 2.5 | Count repos from Step 3 where overall score < 2.5. If count >= 3, recommend MAP. |
| Optimization and Licensing Assessment | OLA | Any repo has Oracle, SQL Server, VMware, or commercial license findings | Check individual report findings for DATA-Q4 (stored procedures / commercial SQL) and INF-Q2 (managed DB) scores. If any repo's findings mention Oracle, SQL Server, VMware, or other commercial database/license references, recommend OLA. |
| Microsoft Modernization Program | MMP | Any repo has .NET or Windows workloads detected | Check APP-Q1 (Programming Languages) findings. If any repo uses C#, .NET, ASP.NET, or VB.NET, recommend MMP. |
| VMware Modernization Program | VMP | Any repo has VMware references in IaC or deployment configs | Check individual report findings for VMware, vSphere, ESXi, or vCenter references. If found, recommend VMP. |
| Windows App Modernization Program | WAMP | Any repo has Windows-based deployment targets | Check individual report findings for Windows Server, IIS, or Windows-specific deployment references. If found, recommend WAMP. |
| Experience-Based Acceleration | EBA | Portfolio has 2+ repos with triggered pathways AND overall score < 3.0 | Count repos with at least one triggered pathway AND overall score < 3.0. If count >= 2, recommend EBA. Specify which pathway(s) are most prevalent for the EBA engagement focus. |
| ISV Workload Migration Program | ISV WMP | Portfolio includes ISV or third-party software workloads | Check findings for references to third-party commercial software, ISV applications, or packaged software deployments. If found, recommend ISV WMP. |

#### 9.2 Program Recommendations Output

For each triggered program:

- **Program name and acronym**
- **Relevance** — Why this program is recommended based on portfolio findings
- **Trigger findings** — Specific portfolio metrics that triggered the recommendation (e.g., "4 of 6 services have overall score < 2.5")
- **What it provides** — Brief description of the program's value
- **Next step** — Recommended action (e.g., "Request MAP engagement via AWS Solutions Architect")

If no programs are triggered, include: "No specific AWS program recommendations based on current findings. As the portfolio evolves, re-assess to identify program eligibility."


### Step 10: Evaluate Portfolio-Level Questions

Evaluate questions that can only be answered by looking across multiple repos. These are distinct from cross-cutting analysis (Step 4) which aggregates individual scores — portfolio-level questions assess capabilities that no individual repo assessment can see.

Individual report scores are never overridden. Where a portfolio-level finding provides context for individual gaps, annotate with "potentially mitigated — verify" but do not change individual scores.

#### 10.1 Portfolio-Level Questions (5)

| ID | Question | Score Rubric | How to Evaluate |
|----|----------|-------------|-----------------|
| PORT-MOD-Q1 | **IaC Standardization** — Are services using a consistent IaC tool across the portfolio? | 4: Single IaC tool across all services. 3: Primary tool covers 80%+, minor exceptions. 2: 2-3 different tools with no standard. 1: No IaC or completely fragmented. | Count distinct IaC tools across repos (Terraform, CDK, CloudFormation, Pulumi, none). Calculate the percentage covered by the most common tool. Factor in the portfolio's preferred IaC tool from preferences. |
| PORT-MOD-Q2 | **Shared Observability Platform** — Is there a centralized observability stack (tracing, logging, metrics) spanning all services? | 4: Centralized tracing + logging + metrics with cross-service correlation. 3: Centralized logging and metrics but no cross-service tracing. 2: Some shared tooling but inconsistent adoption. 1: Each service has independent or no observability. | Check for: shared CloudWatch Log Groups, shared X-Ray/ADOT configuration, shared dashboards, consistent metric namespaces. Cross-reference with individual OPS-Q1 (tracing), OPS-Q2 (SLOs), OPS-Q3 (metrics) scores. |
| PORT-MOD-Q3 | **Dependency Cycle Health** — Are there circular dependencies that block independent modernization? | 4: No circular dependencies. 3: Circular deps exist but are async-only (breakable). 2: Sync circular deps exist with known resolution path. 1: Sync circular deps with no resolution path, blocking modernization. | Using the dependency graph from Step 3, detect cycles. Classify each cycle by dependency type (sync vs async). Sync cycles are harder to break. Score based on severity and resolution feasibility. |
| PORT-MOD-Q4 | **Technology Diversity** — How fragmented is the technology stack across the portfolio? | 4: Low diversity (1-2 languages, 1 IaC tool, 1 DB engine). 3: Moderate diversity (2-3 languages, 1-2 IaC tools). 2: High diversity (4+ languages, 3+ IaC tools, mixed DB engines). 1: Extreme fragmentation with no standardization effort. | Calculate technology diversity score: count distinct languages, IaC tools, DB engines, compute patterns, CI/CD tools. Divide by number of services. Higher ratio = more fragmentation. Factor in preference alignment. |
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


## Report Template

The portfolio MOD report is saved as `portfolio-mod-report.md`. The complete report structure is defined below.

---

### Report Header

```markdown
# Portfolio Modernization Assessment Report

**Date**: <YYYY-MM-DD>
**Services Assessed**: <count>
**Portfolio Context**: <context from additionalPlanContext, or "Not provided">
**Technology Preferences**: Prefer: <prefer list or "None">; Avoid: <avoid list or "None">
```

---

### Executive Dashboard

```markdown
## Executive Dashboard

### Portfolio Score Overview

| Metric | Value |
|--------|-------|
| Portfolio Overall Score | X.X / 4.0 |
| Score Range | X.X – X.X |
| Highest Scoring Service | <name> (X.X) |
| Lowest Scoring Service | <name> (X.X) |
| Pathways Triggered (portfolio-wide) | N of 7 |
| Cross-Cutting Foundational Blockers | N |
| Cross-Cutting Improvement Opportunities | N |

### Readiness Distribution

| Level | Services | Percentage | Description |
|-------|----------|------------|-------------|
| ✅ Mature (3.5–4.0) | N | X% | Fully meets criteria. Minor optimization only. |
| 🟡 Partial (2.5–3.4) | N | X% | Partially meets criteria. Targeted improvements needed. |
| 🟠 Needs Work (1.5–2.4) | N | X% | Significant gaps. Moderate modernization effort. |
| ❌ Not Ready (<1.5) | N | X% | Fundamental gaps. Major modernization required. |

### Category Score Averages

| Category | Portfolio Average | Min | Max | Services with N/A |
|----------|------------------|-----|-----|-------------------|
| Infrastructure & DevOps (INF) | X.X | X.X | X.X | N |
| Application Architecture (APP) | X.X | X.X | X.X | N |
| Data Platform (DATA) | X.X | X.X | X.X | N |
| Security Baseline (SEC) | X.X | X.X | X.X | N |
| Operations & Observability (OPS) | X.X | X.X | X.X | N |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | N | X% |
| infrastructure-only | N | X% |
| deployment-config | N | X% |
| monorepo | N | X% |
| library | N | X% |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | <YYYY-MM-DD> |
| total_services | <N> |
| portfolio_score | <X.X> |
| score_range_min | <X.X> |
| score_range_max | <X.X> |
| mature_services | <N> |
| partial_services | <N> |
| needs_work_services | <N> |
| not_ready_services | <N> |
| pathways_triggered | <N> |
| foundational_blockers | <N> |
| improvement_opportunities | <N> |
| category_inf | <X.X> |
| category_app | <X.X> |
| category_data | <X.X> |
| category_sec | <X.X> |
| category_ops | <X.X> |
| portfolio_level_avg | <X.X> |
```

---

### Technology Stack Summary

```markdown
## Technology Stack Summary

### Programming Languages

| Language | Services | Percentage |
|----------|----------|------------|
| <language> | N | X% |

### Database Engines

| Engine | Type | Services | Managed? |
|--------|------|----------|----------|
| <engine> | Relational / NoSQL / Vector / Cache | N | Yes / No / Mixed |

**Database Distribution**: N managed, N self-managed, N commercial, N open source

### Compute Patterns

| Pattern | Services | Percentage |
|---------|----------|------------|
| <pattern> | N | X% |

### IaC and CI/CD Tools

| Tool | Category | Services |
|------|----------|----------|
| <tool> | IaC / CI/CD | N |

### Standardization Opportunities

<Identify consolidation and standardization opportunities based on technology diversity.
If preferences were provided, note alignment with preferred technologies.>

- <opportunity 1>
- <opportunity 2>
```

---

### Service Dependency Map

```markdown
## Service Dependency Map

<If dependency_overrides were provided:>

### Dependency Overview

| Source Service | Target Service | Type | Coupling | Description |
|---------------|---------------|------|----------|-------------|
| <source> | <target> | sync / async / shared_db / shared_infra | High / Medium / Low | <description> |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Blast Radius | Role | Overall Score |
|---------|--------|---------|--------------|------|---------------|
| <service> | N | N | X% | Foundation / Leaf / Internal | X.X |

### Foundation Services (High Fan-In)

<List services with fan-in >= 3. These must be modernized first.>

### Circular Dependencies

<If circular dependencies detected:>
⚠️ **Circular dependencies detected** — these must be broken in Phase 0:
- Cycle: <Service A> → <Service B> → <Service A>
- <additional cycles>

<If no circular dependencies:>
✅ No circular dependencies detected.

<If dependency_overrides were NOT provided:>

> No dependency information was provided in the portfolio configuration. To enable
> dependency-aware analysis — including coupling scores, blast radius calculation,
> circular dependency detection, and dependency-ordered roadmap phasing — add
> `dependency_overrides` to the portfolio config.
```

---

### Cross-Cutting Concerns

```markdown
## Cross-Cutting Concerns

> Cross-cutting concerns are gaps that appear across multiple services. They are
> classified into two tiers based on score severity.

### 🚨 Foundational Blockers

> Criteria scoring < 2 in 2+ repos. These block all modernization efforts.
> Address these first — nothing else matters until these are resolved.
> **Render this section only if at least one Foundational Blocker is classified. Omit entirely if empty.**

1. **<question_id>: <question topic>** — <N> of <M applicable> services score < 2
   - **Score Distribution**: <list scores per service>
   - **Impact**: <explain how this blocks modernization>
   - **Affected Services**: <list service names>
   - **Portfolio-Level Recommendation**: <coordinated solution>

<Repeat for each Foundational Blocker.>

### 💡 Improvement Opportunities

> Criteria scoring < 3 in 3+ repos. Important but not blocking.
> Address as capacity allows or in parallel with other modernization work.
> **Render this section only if at least one Improvement Opportunity is classified. Omit entirely if empty.**

1. **<question_id>: <question topic>** — <N> of <M applicable> services score < 3
   - **Score Distribution**: <list scores per service>
   - **Impact**: <describe impact>
   - **Affected Services**: <list service names>
   - **Portfolio-Level Recommendation**: <coordinated solution>

<Repeat for each Improvement Opportunity.>
```

If no cross-cutting concerns are identified in either tier:

```markdown
## Cross-Cutting Concerns

No cross-cutting concerns identified. All criteria meet the minimum thresholds across the portfolio.
```

---

### Per-Category Analysis

```markdown
### Per-Category Analysis

> Regardless of the tiered classification above, provide per-category analysis
> for a complete picture of portfolio health.

#### Infrastructure & DevOps

**Portfolio Score: X.X / 4.0**

**Common Patterns:**
- <pattern>: present in N services

**Critical Gaps:**
1. <gap>: affects N services — <recommendation>

#### Application Architecture

**Portfolio Score: X.X / 4.0**

<Analyze common application patterns and gaps>

#### Data Platform

**Portfolio Score: X.X / 4.0**

<Analyze common data patterns and gaps>

#### Security Baseline

**Portfolio Score: X.X / 4.0**

<Analyze common security patterns and gaps>

#### Operations & Observability

**Portfolio Score: X.X / 4.0**

<Analyze common operational patterns and gaps>
```

---

### Dependency-Aware Portfolio Modernization Roadmap

```markdown
## Portfolio Modernization Roadmap

> Dependency-aware phased roadmap with fixed phase names. Services are ordered
> by dependency graph position, then by priority (P0 → P1 → P2), then by score.

### Sequencing Principles

1. **Foundation First**: Shared infrastructure and platform capabilities before service-specific work
2. **Dependency Order**: Upstream services before downstream dependents
3. **Risk Mitigation**: High-risk changes sequenced to minimize blast radius
4. **Parallel Tracks**: Independent services can be modernized concurrently
5. **Quick Wins**: Early wins build momentum and demonstrate value

### Phase 0 — Cross-Cutting Foundation (Mo 0–1)

**Objective**: Establish shared capabilities, break circular dependencies, and address portfolio-wide blockers.

**Cross-Cutting Activities:**
- <Foundational Blocker remediation from Step 5>
- <Circular dependency breaking from Step 4.4>
- <Shared infrastructure improvements>

**Organizational Enablers:**
- Training: <topics based on skill gaps>
- Tooling: <tools to standardize>
- Standards: <standards to establish>

**Estimated Effort**: High / Medium / Low

### Phase 1 — Quick Wins (Mo 1–2)

**Objective**: Modernize foundation services and establish patterns.

**Services in Scope:**
1. **<Service Name>** (P0, Score: X.X / 4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
     - <activity 2>
   - Dependencies: None (foundation service)
   - Blocks: <services waiting on this one>
   - Estimated Effort: High / Medium / Low

<Repeat for each Phase 1 service, ordered by priority then fan-in.>

**Expected Outcomes:**
- <outcome 1>
- <outcome 2>

### Phase 2 — Foundation (Mo 2–4)

**Objective**: Modernize services that depend on Phase 1 services. Replicate proven patterns.

**Services in Scope:**
1. **<Service Name>** (P1, Score: X.X / 4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
     - <activity 2>
   - Dependencies: <Phase 1 services>
   - Blocks: <services waiting on this one, or "None">
   - Estimated Effort: High / Medium / Low

<Repeat for each Phase 2 service.>

**Parallel Tracks:**
- <Services that can be modernized concurrently>

### Phase 3 — Advanced (Mo 4–6+)

**Objective**: Optimize leaf services, implement advanced capabilities, continuous improvement.

**Services in Scope:**
1. **<Service Name>** (P2, Score: X.X / 4.0)
   - Current State: <summary>
   - Target State: <summary>
   - Key Activities:
     - <activity 1>
   - Dependencies: <Phase 2 services>
   - Estimated Effort: High / Medium / Low

<Repeat for each Phase 3 service.>

### Total Portfolio Effort

**Total Estimated Effort**: High / Medium / Low
**Expected Timeline**: X months (with Y parallel tracks)
```


---

### AWS Modernization Pathways

```markdown
## AWS Modernization Pathways

> The AWS Modernization Pathways framework recognizes there is no "one-size-fits-all"
> approach. A customer portfolio may be divided into multiple pathways depending on
> workloads and priorities; these pathways can be executed in parallel.

### Portfolio Pathway Summary

| Pathway | Services Triggered | % of Portfolio | Priority | Est. Effort |
|---------|--------------------|----------------|----------|-------------|
| Move to Cloud Native | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Containers | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Open Source | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Managed Databases | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Managed Analytics | N | X% | High / Medium / Low | High / Medium / Low |
| Move to Modern DevOps | N | X% | High / Medium / Low | High / Medium / Low |
| Move to AI | N | X% | High / Medium / Low | High / Medium / Low |

### Portfolio Pathway Aggregation

This table shows exactly which repositories fall into each pathway status, providing
a single at-a-glance view of pathway coverage across the portfolio. Each repo appears
in exactly one column per pathway row.

| Pathway | Triggered | Not Triggered | Not Applicable |
|---------|-----------|---------------|----------------|
| Move to Cloud Native | <comma-separated repo names or "—"> | <comma-separated repo names or "—"> | <comma-separated repo names or "—"> |
| Move to Containers | ... | ... | ... |
| Move to Open Source | ... | ... | ... |
| Move to Managed Databases | ... | ... | ... |
| Move to Managed Analytics | ... | ... | ... |
| Move to Modern DevOps | ... | ... | ... |
| Move to AI | ... | ... | ... |

### Per-Service Pathway Assignment

| Service | Cloud Native | Containers | Open Source | Managed DB | Managed Analytics | Modern DevOps | Move to AI |
|---------|-------------|------------|-------------|------------|-------------------|---------------|------------|
| <service> | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A | ✅ / — / N/A |

### Pathway Dependencies and Parallel Execution

**Sequential Dependencies:**
- Move to Containers should precede Move to Cloud Native (containerize before decomposing)
- Move to Open Source may precede Move to Managed Databases (migrate off proprietary first)
- Move to Modern DevOps enables faster execution of all other pathways (CI/CD accelerates delivery)
- Move to Managed Databases is often a prerequisite for Move to AI (data foundations needed)

**Parallel Execution Tracks:**
- **Track 1**: <pathways that can run concurrently>
- **Track 2**: <pathways that can run concurrently>

### Pathway Details

<For each triggered pathway, include a subsection:>

#### Move to <Pathway Name>

- **Services Affected**: <list> (N total)
- **Portfolio Priority**: High / Medium / Low
- **Common Trigger Criteria**:
  - <criterion ID> score < X: affects N services
  - <criterion ID> score < X: affects N services
- **Representative AWS Services**: <list, steered by preferences if provided>
- **Key Activities**:
  1. <portfolio-level activity>
  2. <per-service activity>
- **Cross-Service Synergies**: <shared patterns, reusable templates, common tooling>
- **Estimated Effort**: High / Medium / Low across N services
- **Roadmap Phase Alignment**: Phase 0 / 1 / 2 / 3
- **Relevant Learning Materials**: Module X — <module name>

<Repeat for each triggered pathway.>

<For the Move to AI pathway specifically, include the contextual guard suppression summary:>

#### Move to AI

- **Services Affected**: <list> (N total)
- **Portfolio Priority**: High / Medium / Low
- **Aggregation**: Move to AI: Triggered in X of Y services (Z services had no AI intent in context — pathway correctly suppressed)
- **Not Triggered Breakdown**:
  - Contextual guard suppression (no AI intent): <list of services or "—">
  - Already present (AI frameworks detected): <list of services or "—">
- **Common Trigger Criteria**:
  - <criterion ID> score < X: affects N services
- **Representative AWS Services**: <list, steered by preferences if provided>
- **Key Activities**:
  1. <portfolio-level activity>
  2. <per-service activity>
- **Cross-Service Synergies**: <shared patterns, reusable templates, common tooling>
- **Estimated Effort**: High / Medium / Low across N services
- **Roadmap Phase Alignment**: Phase 3
- **Relevant Learning Materials**: Module 7 — Move to AI
```

---

### Integration Opportunities

```markdown
## Integration Opportunities

### Shared Service Extraction

<Identify common functionality that could be extracted into shared services.>

**Opportunity: <service name>**
- **Current State**: Duplicated in <list services>
- **Proposed Solution**: <shared service proposal, steered by preferences>
- **Benefits**: <benefits>
- **Effort**: High / Medium / Low
- **Priority**: High / Medium / Low

### Event-Driven Architecture

<Identify opportunities to replace sync calls with async events.>

**Opportunity: <integration name>**
- **Current State**: <service A> calls <service B> synchronously
- **Proposed Solution**: Event-driven with <technology, steered by preferences>
- **Benefits**: <benefits>
- **Effort**: High / Medium / Low

### API Gateway Consolidation

<Identify opportunities for unified API management.>

### Observability Unification

<Identify opportunities for standardized observability.>
```

---

### Risk Assessment

```markdown
## Risk Assessment

### Risk Matrix

| Risk | Likelihood | Impact | Priority | Mitigation | Phase |
|------|------------|--------|----------|------------|-------|
| <risk description> | High / Medium / Low | High / Medium / Low | 🔴 Critical / 🟠 High / 🟡 Medium / 🟢 Low | <mitigation strategy> | Phase 0 / 1 / 2 / 3 |

### High-Risk Dependencies

<List services with score < 2.0 AND fan-in >= 3.>

### Single Points of Failure

<List services with blast radius >= 50% and no redundancy.>

### Circular Dependency Risks

<List all circular dependencies and their resolution plan.>

### Data Availability Risks

<List services with self-managed databases AND high fan-in.>

### Observability Blind Spots

<List services without tracing AND high fan-out.>
```

---

### Resource Allocation Recommendations

```markdown
## Resource Allocation Recommendations

### Team Structure

**Recommended Approach**: <centralized platform team + service teams / federated model>

**Platform Team**:
- Responsibilities: Shared infrastructure, platform capabilities, standards
- Skills Required: <skills>

**Service Teams**:
- Responsibilities: Service-specific modernization
- Skills Required: <skills>

### Skill Gaps

| Skill | Required For | Currently Available? | Priority |
|-------|-------------|---------------------|----------|
| <skill> | <activities> | Yes / No / Partial | High / Medium / Low |

### Training Recommendations

<Recommend training programs based on common gaps. Reference learning materials below.>

### External Support

<Recommend where AWS Professional Services or consulting partners could accelerate.>
```

---

### AWS Programs & Engagement Recommendations

```markdown
## AWS Programs & Engagement Recommendations

> **This section appears ONLY in portfolio reports, NEVER in individual reports.**
> Programs are engagement-level decisions scoped to the customer's overall estate.

### Recommended Programs

| Program | Acronym | Relevance | Trigger Findings | Next Step |
|---------|---------|-----------|-----------------|-----------|
| <program name> | <acronym> | <why recommended> | <specific findings> | <recommended action> |

> If no programs are triggered:
> "No specific AWS program recommendations based on current findings. As the
> portfolio evolves, re-assess to identify program eligibility."

### Program Details

<For each recommended program, provide a brief paragraph explaining:>
- Why this program was recommended (which specific findings triggered it)
- What the program provides
- Suggested timing relative to the modernization roadmap phases

> These are engagement-level recommendations. Discuss with your AWS Solutions Architect
> or Partner to determine eligibility and timing.
```

---

### Learning Materials

```markdown
## Recommended Self-Paced Learning Materials

> Include relevant links only from the following categories based on portfolio-wide
> skill gaps identified in the Resource Allocation section and triggered pathways.

<Include only modules relevant to the portfolio's triggered pathways and skill gaps.>
```

**Module 2: Move to Cloud Native (Containers and Serverless):**
- Cloud Design Patterns, Architectures, and Implementations — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/introduction.html
  - Essential reference for microservices decomposition: Strangler Fig, Anti-corruption Layer, Saga patterns, Event Sourcing, Circuit Breaker, API routing, Hexagonal Architecture, and more
- AWS Modernization Pathways: Move to Cloud Native Serverless — https://skillbuilder.aws/learning-plan/CMK2J48MVN/aws-modernization-pathways-move-to-cloud-native-serverless-includes-labs/EFUPP53B4Q
- Lambda Foundations — https://skillbuilder.aws/learn/XHRS91KKK6/aws-lambda-foundations/R85JRN3APC
- Architecting Serverless Applications — https://skillbuilder.aws/learn/MRWENY7FSX/architecting-serverless-applications/QVFY2JHVEH
- Amazon API Gateway for Serverless Applications — https://skillbuilder.aws/learn/GQA6FHWPJD/amazon-api-gateway-for-serverless-applications/JVRZ3PSW4H
- Deploying Serverless Applications — https://skillbuilder.aws/learn/M531VCW415/deploying-serverless-applications/SMY21G7FYZ
- Introduction to Amazon DynamoDB (Lab) — https://skillbuilder.aws/learn/6DYXN7K7ZQ/lab--introduction-to-amazon-dynamodb/GZ3EU55RYJ
- Amazon DynamoDB for Serverless Architecture — https://skillbuilder.aws/learn/SY1Y83VKTB/amazon-dynamodb-for-serverless-architectures/K9NM3PHH3S
- Modernize a Monolith to ECS and Fargate using Application Discovery — https://skillbuilder.aws/learn/1YXAWYH2WA/modernize-a-monolith-to-ecs-and-fargate-using-application-discovery/AQ37WHN3K1
- Meeting Simulator: Transform Monolithic App into Serverless Microservices — https://skillbuilder.aws/learn/HUKQHYU9TB/meeting-simulator-transforming-our-monolithic-app-into-serverless-microservices/NS6S2J7YR7

**Module 3: Move to Containers with Amazon ECS and EKS:**
- AWS Modernization Pathways: Move to Containers with Amazon EKS — https://skillbuilder.aws/learning-plan/GNYBZ9X9EM/aws-modernization-pathways-move-to-containers-with-amazon-eks-includes-labs/1HB9MKXD2N
- AWS Modernization Pathways: Move to Containers with Amazon ECS — https://skillbuilder.aws/learning-plan/CDA8Y4JRRR/aws-modernization-pathways-move-to-containers-with-amazon-ecs-includes-labs/1UB9AW4KYN
- Introduction to Containers — https://skillbuilder.aws/learn/CUCA1DK47V/introduction-to-containers/XJ58VC1FF5
- AWS Fargate Getting Started — https://skillbuilder.aws/learn/6QS9CM1V7K/aws-fargate-getting-started/EDX6V7B5YR
- Amazon ECR Getting Started — https://skillbuilder.aws/learn/M494WWS5EF/amazon-ecr-getting-started/N5CQ7DC6HT
- Amazon EKS Primer — https://skillbuilder.aws/learn/Z521GMBP1J/amazon-eks-primer/NGM5AF9K72
- Deploy Applications on Amazon EKS (Lab) — https://skillbuilder.aws/learn/2B5XUE2V9C/lab--deploy-applications-on-amazon-elastic-kubernetes-service-eks/SM5HZNTY9J
- Amazon ECS Getting Started — https://skillbuilder.aws/learn/CY2F57HH7V/amazon-ecs-getting-started/4QUDNRVSNC
- Working with Amazon Elastic Container Service (Lab) — https://skillbuilder.aws/learn/CV6ZEU3NHE/working-with-amazon-elastic-container-service/X989GB8H74
- EKS Workshop — https://www.eksworkshop.com/
- EKS Auto Mode Workshop — https://catalog.workshops.aws/workshops/aadbd25d-43fa-4ac3-ae88-32d729af8ed4

**Module 4: Move to Managed Databases:**
- AWS Modernization Pathways: Move to Managed Databases — https://skillbuilder.aws/learning-plan/VNJ8FZ3ZRC/aws-modernization-pathways-move-to-managed-databases-includes-labs/2S2QZKG9DV
- Introduction to Building with AWS Databases — https://skillbuilder.aws/learn/HYKKWEN9ZS/introduction-to-building-with-aws-databases/V7RVH2KY91
- Selecting your Data Migration Strategy with AWS — https://skillbuilder.aws/learn/RKGP54WJPP/selecting-your-data-migration-strategy-with-aws/D38U3CZEYR
- AWS Database Migration Service (DMS) Getting Started — https://skillbuilder.aws/learn/ND246G8Y3W/aws-database-migration-service-aws-dms-getting-started/QK5CCBP464
- Introduction to AWS Database Migration Service (Lab) — https://skillbuilder.aws/learn/CX63W1TFSH/introduction-to-aws-database-migration-service/3DJVXSU4SE
- Amazon RDS for Oracle Getting Started — https://skillbuilder.aws/learn/YMYMJUMAET/amazon-rds-for-oracle-getting-started/74GQB3CA9U
- Amazon RDS for SQL Server Getting Started — https://skillbuilder.aws/learn/WSV85JHZFF/amazon-rds-for-sql-server-getting-started/E446MXPEYH
- Migrating RDS MySQL to Aurora (Lab) — https://skillbuilder.aws/learn/RZF2GBUUWX/migrating-rds-mysql-to-aurora-with-read-replica/SMG825PXTK
- Amazon DocumentDB Getting Started — https://skillbuilder.aws/learn/5RTP1DW5WQ/amazon-documentdb-with-mongodb-compatibility-getting-started/JDFWRT5GPD
- Amazon Keyspaces Getting Started — https://skillbuilder.aws/learn/KHGZNGWXKV/amazon-keyspaces-getting-started/MXK17GET8G
- Amazon RDS for MariaDB Getting Started — https://skillbuilder.aws/learn/DAFQM637NV/amazon-rds-for-mariadb-getting-started/N2Z47FGXSE
- AWS PartnerCast: Vector Databases for Generative AI Applications — https://skillbuilder.aws/learn/UQ74USQJHU/aws-partnercast--vector-databases-for-generative-ai-applications--technical/7DKMBAPCST

**Module 5: Move to Managed Analytics:**
- AWS Modernization Pathways: Move to Managed Analytics — https://skillbuilder.aws/learning-plan/RWZA84NMVV/aws-modernization-pathways-move-to-managed-analytics--includes-labs/9BAKK2QQQU

**Module 6: Move to Modern DevOps:**
- AWS Modernization Pathways: Move to Modern DevOps — https://skillbuilder.aws/learning-plan/1FGEQKGPQD/aws-modernization-pathways-move-to-modern-devops-includes-labs/MNQZ2KPVCK
- Getting Started with DevOps on AWS — https://skillbuilder.aws/learn/R4B13K95YQ/getting-started-with-devops-on-aws/38NHHYRV1R
- Working with AWS CodeCommit — https://skillbuilder.aws/learn/SH4UVGQX6S/working-with-aws-codecommit/Y9UGFPK95M
- Create a CI/CD Pipeline to Deploy Your App to AWS Fargate (ECS) — https://skillbuilder.aws/learn/H61B17Z8R7/create-a-cicd-pipeline-to-deploy-your-app-to-aws-fargate/T66BGGGHV5
- AWS CloudFormation Getting Started — https://skillbuilder.aws/learn/RH22P2RXU4/aws-cloudformation-getting-started/KEK5BT6HSE
- Advanced Testing Practices Using AWS DevOps Tools — https://skillbuilder.aws/learn/1YC7UXUWBR/advanced-testing-practices-using-aws-devops-tools/A32U6G7NEQ
- Monitor Java Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/PMCTXKYK1Y/monitor-java-applications-using-amazon-cloudwatch-application-signals/15ZK4ETKE9
- Monitor .NET Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/255DDEDPV5/monitor-net-applications-using-amazon-cloudwatch-application-signals/1WZ1NT16HJ
- Monitor Python Applications Using Amazon CloudWatch Application Signals — https://skillbuilder.aws/learn/JMPDZD64MV/monitor-python-applications-using-amazon-cloudwatch-application-signals/2JP3J2MPCK
- AWS Developer: CI/CD Automation — https://skillbuilder.aws/learn/C1KF8ZJ1D8/aws-developer--cicd-automation/KY1E1JS9FA
- AWS PartnerCast: Automate EKS Deployments With GitOps Using ArgoCD and GitHub Actions — https://skillbuilder.aws/learn/D9U7XMXP31/aws-partnercast--tech-talks--automate-eks-deployments-with-gitops-using-argocd-and-github-actions--technical/Z4M9Z8FY88
- AWS PartnerCast: Next-Gen Platform Engineering: Combining EKS, GitOps & Amazon Q for Intelligent DevOps — https://skillbuilder.aws/learn/FJBV2YWNSS/aws-partnercast--tech-talks--nextgen-platform-engineering-combining-eks-gitops--amazon-q-for-intelligent-devops--technical/NZ284HRTVG
- AWS PartnerCast: Unleash Innovation with a Cloud Operating Model and Platform Engineering — https://skillbuilder.aws/learn/EG2A78NXEC/aws-partnercast--tech-talks--unleash-innovation-with-a-cloud-operating-model-and-platform-engineering--technical/CC8ZTK88QK
- EKS Workshop: Automation — https://www.eksworkshop.com/docs/automation/
- EKS SaaS GitOps Workshop — https://catalog.workshops.aws/eks-saas-gitops/en-US/03-lab1

**Module 7: Move to AI:**
- AWS Modernization Pathways: Move to AI — https://skillbuilder.aws/learning-plan/VDFEE4ACCV/aws-modernization-pathways-move-to-ai-pathways-includes-labs/P3DAWPTN63
- Introduction to Generative AI: Art of the Possible — https://skillbuilder.aws/learn/ZEVZZ1D4AS/introduction-to-generative-ai--art-of-the-possible/Y7MTGJCW1U
- Planning a Generative AI Project — https://skillbuilder.aws/learn/HU1FQRGDDZ/planning-a-generative-ai-project/SYR3SCPSHC
- Amazon Bedrock Getting Started — https://skillbuilder.aws/learn/63KTRM86DQ/amazon-bedrock-getting-started/SC2Y3HMAUE
- Essentials for Prompt Engineering — https://skillbuilder.aws/learn/XBNAVKA88J/essentials-of-prompt-engineering/9T9Q45EDTV
- AWS SimuLearn: Prompt Engineering with Amazon Bedrock — https://skillbuilder.aws/learn/FC13FQVQYG/aws-simulearn-prompt-engineering-with-amazon-bedrock/QDGW58VYHP
- Optimizing Foundation Models — https://skillbuilder.aws/learn/CDYTAJCKGY/optimizing-foundation-models/PVR1FRGN1T
- Build and Evaluate Retrieval Augmented Generation (RAG) Applications using Knowledge Bases for Amazon Bedrock (Lab) — https://skillbuilder.aws/learn/JRGWCFYT67/lab--build-and-evaluate-retrieval-augmented-generation-rag-applications-using-knowledge-bases-for-amazon-bedrock/A4MN58JB7A
- Amazon Q Developer Getting Started — https://skillbuilder.aws/learn/BQMRXE8AB4/amazon-q-developer-getting-started/JY4XXGZDJA
- Re-imagine Developer Experience using Amazon Q Developer (Lab) — https://skillbuilder.aws/learn/F7D8YHMVYK/lab--reimagine-developer-experience-using-amazon-q-developer/ZWRC749F68
- Introduction to Agentic AI on AWS — https://skillbuilder.aws/learn/DNBD5MT8ZD/introduction-to-agentic-ai-on-aws/WAKAFK6UFY
- DevOps and AI on AWS: CloudWatch Anomaly Detection (Lab) — https://skillbuilder.aws/learn/RWYVJ73MXP/lab--devops-and-ai-on-aws-cloudwatch-anomaly-detection/BRPDNZUGU7
- Introduction to AWS DevOps Agent (Lab) — https://skillbuilder.aws/learn/2BMGKG58ZU/introduction-to-aws-devops-agent/S61EE8J7S9
- Creating an AWS DevOps AI Agent with the Strands Agents SDK (Lab) — https://skillbuilder.aws/learn/AH1GD8AJY3/lab--creating-an-aws-devops-ai-agent-with-the-strands-agents-sdk/A9SKJNMPJ2
- AWS PartnerCast: Deep Dive: Building Observable AI Agents with Strands, Amazon Bedrock Agent Core & SageMaker MLflow — https://skillbuilder.aws/learn/1EN76TZBB6/aws-partnercast--deep-dive-building-observable-ai-agents-with-strands-amazon-bedrock-agent-core--sagemaker-mlflow--technical/CX2K6XAT84

Only include links from categories that are relevant to the portfolio-wide gaps and triggered pathways found in this assessment.


---

### Portfolio-Level Findings

```markdown
## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual scores). Individual report scores are never overridden.

### <question_id>: <question topic>

- **Score**: <1-4>
- **Finding**: <what was observed across the portfolio>
- **Evidence**: <specific repos, files, or configurations>
- **Recommendation**: <portfolio-level action>
- **Contextual Annotations**: <any individual concerns this provides context for, with "verify" instructions>

<Repeat for each of the 5 portfolio-level questions (PORT-MOD-Q1 through PORT-MOD-Q5).>
```

---

### Service-by-Service Summary

```markdown
## Service-by-Service Summary

| Service | Repo Type | Priority | Overall Score | INF | APP | DATA | SEC | OPS | Pathways Triggered | Phase |
|---------|-----------|----------|---------------|-----|-----|------|-----|-----|--------------------|-------|
| <service> | <repo_type> | P0/P1/P2 | X.X | X.X | X.X | X.X | X.X | X.X | N of 7 | 0/1/2/3 |

### Individual Service Details

#### <Service Name>

- **Overall Score**: X.X / 4.0
- **Repository Type**: <repo_type>
- **Priority**: <P0/P1/P2 or "Not set">
- **Assessment Date**: <YYYY-MM-DD>
- **Category Scores**:
  - Infrastructure & DevOps: X.X
  - Application Architecture: X.X
  - Data Platform: X.X
  - Security Baseline: X.X
  - Operations & Observability: X.X
- **Top Gaps**:
  - <question_id>: score X — <brief finding summary>
  - <question_id>: score X — <brief finding summary>
  - <question_id>: score X — <brief finding summary>
- **Triggered Pathways**: <list of triggered pathway names>
- **Key Recommendations**:
  - <top 1–3 recommendations for this service>

<If dependency information is available:>
- **Depends On**: <list of services this service depends on>
- **Depended On By**: <list of services that depend on this service>
- **Blast Radius**: X%
- **Roadmap Phase**: Phase X — <phase name>

<Repeat for each service, ordered by: overall score (lowest first), then by priority (P0 first).>
```

---

### Assessment Inventory

```markdown
## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Overall Score |
|---|---------|-------------|-----------------|-----------|---------------|
| 1 | <service name> | <file path> | <date> | <repo_type> | X.X |
```

---

### Table of Contents

The complete report structure, for reference:

```markdown
# Portfolio Modernization Assessment Report

1. Executive Dashboard
   - Portfolio Score Overview
   - Readiness Distribution
   - Category Score Averages
   - Repo Type Distribution
   - Readiness Snapshot
2. Technology Stack Summary
3. Service Dependency Map
4. Cross-Cutting Concerns
   - Foundational Blockers
   - Improvement Opportunities
   - Per-Category Analysis
5. Portfolio Modernization Roadmap
   - Phase 0 — Cross-Cutting Foundation
   - Phase 1 — Quick Wins
   - Phase 2 — Foundation
   - Phase 3 — Advanced
6. AWS Modernization Pathways
   - Portfolio Pathway Summary
   - Portfolio Pathway Aggregation
   - Per-Service Pathway Assignment
   - Pathway Dependencies and Parallel Execution
   - Pathway Details
7. Integration Opportunities
8. Risk Assessment
9. Resource Allocation Recommendations
10. AWS Programs & Engagement Recommendations
11. Recommended Self-Paced Learning Materials
12. Portfolio-Level Findings
13. Service-by-Service Summary
14. Assessment Inventory
```

## Constraints and Guardrails

Strictly follow these rules at all times:

- **Read-only assessment**: Do not modify any source code, configuration, or infrastructure. Only create the output portfolio report file.
- **Minimum 2 reports**: The portfolio assessment requires at least 2 valid MOD reports. Terminate with a clear error if fewer than 2 are found.
- **N/A exclusion**: Scores of N/A are excluded from portfolio-level category averages (both numerator and denominator), overall score calculations, and cross-cutting concern analysis. A question that is N/A for a service does not count as a gap for that service.
- **Two-tier classification only**: Cross-cutting concerns use exactly two tiers — Foundational Blockers (score < 2 in 2+ repos) and Improvement Opportunities (score < 3 in 3+ repos).
- **Fixed phase names**: Roadmap phases are always named Cross-Cutting Foundation, Quick Wins, Foundation, and Advanced.
- **Dependency-aware ordering**: When dependency information is available, services must not be assigned to a phase earlier than their dependencies. Foundation services (high fan-in) go in Phase 1 or earlier. Within phases, order by priority (P0 → P1 → P2).
- **Preferences for framing only**: Technology preferences (prefer/avoid) influence recommendation language and technology suggestions. They do NOT change scores, N/A mappings, pathway trigger logic, or cross-cutting concern classification.
- **Evidence-based**: All cross-cutting findings must reference specific question IDs and service names. Do not make vague claims — state which services are affected and which questions triggered the finding.
- **All 7 pathways in aggregation**: The pathway aggregation table must include all 7 pathways, even if none are triggered. Every assessed repo must appear in exactly one column per pathway row.
- **Report completeness**: The output report must contain all required sections: executive dashboard, technology stack summary, service dependency map, cross-cutting concerns, phased roadmap, pathway aggregation, integration opportunities, risk assessment, resource allocation, AWS programs, learning materials, service-by-service summary, and assessment inventory.
