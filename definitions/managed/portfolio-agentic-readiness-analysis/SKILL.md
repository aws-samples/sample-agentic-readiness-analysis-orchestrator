---
name: portfolio-agentic-readiness-analysis
description: Aggregates per-repo ARA reports into portfolio-level cross-cutting analysis
type: managed
---

## Name

Portfolio Agentic Readiness Analysis

## Objective

Aggregate individual repository Agentic Readiness Analysis (ARA) reports into a portfolio-level analysis that identifies cross-cutting blockers, shared risks, service dependency patterns, and portfolio-wide remediation guidance — enabling coordinated agentic readiness across the entire service estate.

## Summary

This transformation consumes multiple individual ARA report JSON artifacts (`*-ara-report.json` files) from different repositories and produces a comprehensive portfolio-level view focused exclusively on agentic readiness. It performs intelligent discovery and parsing of ARA report JSONs, identifies cross-cutting BLOCKERs and RISKs that appear across multiple services, constructs a service dependency map from portfolio configuration, generates portfolio-level remediation guidance, recommends agentic enablement programs, and produces a service-by-service summary.

The transformation follows a 9-step pipeline:
1. **Read Context** (Step 0): Parse additionalPlanContext for portfolio framing
2. **Discovery** (Step 1): Locate all ARA report files in the directory structure
3. **Parsing** (Step 2): Extract readiness profiles, severity counts, and per-question findings from each report
4. **Executive Dashboard** (Step 3): Build readiness distribution across the portfolio
5. **Cross-Cutting BLOCKERs** (Step 4): Identify BLOCKERs appearing in 2+ repos
6. **Cross-Cutting RISKs** (Step 4b): Identify RISKs meeting the scaling threshold (max(3, 33% of applicable repos)), split by RISK-SAFETY and RISK-QUALITY tiers
7. **Dependency Mapping** (Step 5): Construct service dependency map from dependency_overrides
8. **Remediation Guidance** (Step 6): Generate portfolio-level remediation for cross-cutting BLOCKERs
9. **Agentic Programs** (Step 7): Recommend AI DLC, AXE, Innovation EBA where triggered
10. **Portfolio-Level Questions** (Step 8): Evaluate PORT-ARA-Q1 through PORT-ARA-Q5 — capabilities only visible across multiple repos

The output is a **four-artifact bundle** containing:
- `{portfolio_name}-portfolio-ara-report.md` — richest narrative
- `{portfolio_name}-portfolio-ara-report.json` — canonical machine-readable contract
- `{portfolio_name}-portfolio-ara-report.html` — single self-contained HTML visualization
- `{portfolio_name}-portfolio-ara-report.metadata.json` — version compatibility sidecar

The MD report contains:
- Executive dashboard with readiness distribution by profile
- Blocker heatmap by section (which dimensions block the most repos)
- Readiness snapshot (structured, machine-parseable metrics for dashboard consumption)
- Cross-cutting BLOCKERs (same blocker question in 2+ repos)
- Cross-cutting RISKs (same risk question appearing in max(3, 33% of applicable repos))
- Service dependency map from dependency_overrides
- Portfolio-level remediation guidance for cross-cutting blockers
- Agentic program recommendations (AI DLC, AXE, Innovation EBA)
- Service-by-service summary (repo name, profile, blocker count, risk count)

This portfolio TD focuses exclusively on cross-cutting BLOCKER/RISK identification across multiple ARA reports. It does not include modernization pathways, roadmap phases, numeric scores, technology preferences, or resource allocation recommendations.

## Entry Criteria

- At least 2 individual ARA report JSON artifacts exist in repository directories
- ARA report JSONs follow the expected schema: `analysis_type == "ara"`, `classification` object, `findings[]` array with per-finding 12-field shape
- Reports are accessible at specified paths or in a common directory structure
- Write permissions exist to create the output directory and portfolio artifact bundle (MD, JSON, HTML, and metadata.json)

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning discovery, read the portfolio analysis context from `additionalPlanContext` to extract framing information and service configuration.

#### 0.1 Read Portfolio Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `portfolio_name` | string | Yes | — | Identifier for the portfolio. Used to name the output bundle (`{portfolio_name}-portfolio-ara-report.{md,json,html,metadata.json}`) and to populate report headers and metadata. If absent, terminate with `"Portfolio analysis failed: portfolio_name is required in additionalPlanContext."` |
| `context` | string | No | — | Free-text description of the portfolio (e.g., "E-commerce platform with 5 microservices migrating to agentic integration"). Used to frame portfolio-level remediation guidance and recommendations. |
| `service_inventory` | object[] | No | — | List of services in the portfolio with metadata (name, path, priority, repo_type, agent_scope, tags). Used to enrich the service-by-service summary and cross-reference with discovered reports. |
| `dependency_overrides` | object[] | No | — | Explicit service dependency declarations. Each entry has: `source` (service name), `target` (service name), `type` (sync, async, shared_db, shared_infra), and `description`. Used to build the service dependency map in Step 5. |

**Example `additionalPlanContext`:**

```yaml
additionalPlanContext: |
  context: "E-commerce platform with 5 microservices evaluating agentic readiness for customer support automation"
  service_inventory:
    - name: "order-service"
      path: "../order-service"
      priority: "P0"
      repo_type: "application"
      agent_scope: "write-enabled"
    - name: "catalog-service"
      path: "../catalog-service"
      priority: "P1"
      repo_type: "application"
      agent_scope: "read-only"
    - name: "infra-modules"
      path: "../infra-modules"
      priority: "P2"
      repo_type: "infrastructure-only"
      agent_scope: "read-only"
  dependency_overrides:
    - source: "order-service"
      target: "catalog-service"
      type: "sync"
      description: "REST API call to look up product details"
    - source: "order-service"
      target: "payment-service"
      type: "sync"
      description: "Payment processing via REST"
```

#### 0.2 Apply Defaults

- **`context`** → No default. If absent, portfolio-level recommendations are written without additional framing.
- **`service_inventory`** → No default. If absent, service metadata is derived solely from discovered reports.
- **`dependency_overrides`** → No default. If absent, the service dependency map section notes that no dependency information was provided and recommends the user supply it for richer analysis.

### Step 1: Discovery — Locate ARA Reports

Scan the target directory structure to find all individual ARA report JSON artifacts.

#### 1.1 Discovery Process

- Recursively search for files matching the pattern `*-ara-report.json` in the directory tree
- For each report found, extract the project/service name from the filename (the prefix before `-ara-report.json`)
- Extract the repository path (parent directory or grandparent directory of the report file)
- Create an inventory of all services assessed with their JSON file locations
- Validate minimum requirement: at least 2 reports must be discovered

**Input Options:**
- A parent directory containing multiple repository folders, each with an ARA report, OR
- A list of explicit paths to ARA report JSON files (from `service_inventory` paths)

#### 1.2 Validation

- Verify each discovered file exists and is readable
- Verify each file is a valid JSON document
- Verify each file is the expected ARA report shape:
  - Has `analysis_type == "ara"` at the root
  - Has a `classification` object with `tier`, `blocker_count`, `risk_safety_count`
  - Has a `findings[]` array with question IDs (API-Q1 through ENG-Q5) and the 12 per-finding fields
  - Has a `metadata` object with `analysis_type` and `td_version`
- Exclude files that don't match the expected shape — log a warning for each excluded file
- Log warnings for inaccessible or malformed files
- **Terminate with a clear error if fewer than 2 valid ARA reports are found**

#### 1.3 Build Report Inventory

After discovery, compile a structured inventory:

| Field | Source |
|-------|--------|
| Service name | Extracted from filename prefix (or `metadata.repo_name` if present) |
| Report file path | Full path to the `*-ara-report.json` file |
| Repository path | Parent directory of the report |
| Priority | From `service_inventory` if available, otherwise from `metadata.priority` in the JSON if present |
| Repo type | From `metadata.repo_type` in the JSON |
| Agent scope | From `metadata.agent_scope` in the JSON |

Cross-reference discovered reports with `service_inventory` (if provided) to enrich metadata. If a service appears in `service_inventory` but no report is found, log a warning: "Service '{name}' listed in service_inventory but no ARA report found at expected path."

### Step 2: Parse Individual ARA Reports

For each ARA report JSON found, extract the data needed for portfolio-level analysis.

#### 2.1 Service Metadata

Extract from the JSON `metadata` object at the root:

- **Service/repository name** — from `metadata.repo_name` (or derive from the filename)
- **Analysis date** — from `metadata.analysis_date` (validate YYYY-MM-DD format)
- **Repo type** — from `metadata.repo_type` (one of: `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`). If absent, assume `application`.
- **Agent scope** — from `metadata.agent_scope` (one of: `read-only`, `write-enabled`). If absent, assume `read-only`.

#### 2.2 Readiness Profile

Extract the classification from the JSON `classification` object at the root:

- **Profile** — from `classification.tier` (+ `classification.sub_qualifier` when present). One of: `Agent-Ready`, `Pilot-Ready`, `Pilot-Ready (Safety Concerns)`, `Remediation Required`, `Not Agent-Integrable`
- **Blocker count** — from `classification.blocker_count`
- **Risk-safety count** — from `classification.risk_safety_count`
- **Risk-quality count** — from `classification.risk_quality_count`
- **Info count** — from `classification.info_count`

#### 2.3 Detailed Findings (Per-Question)

From the JSON `findings[]` array, extract for each entry:

- **Question ID** — `findings[i].question_id` (e.g., API-Q1, AUTH-Q7, ENG-Q3)
- **Native severity** — `findings[i].ara_metadata.native_severity` (BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO)
- **Unified severity** — `findings[i].severity` (High / Medium / Low)
- **Finding description** — `findings[i].description`
- **Gap** — `findings[i].gap`
- **Recommendation** — `findings[i].recommendation`
- **Evidence** — `findings[i].evidence` ({file, lines} or null)
- **Safety impact** — `findings[i].safety_impact` (boolean)

From the JSON `evaluations[]` array (if present), extract entries for questions that resolved to N/A, Not Evaluated (extended), or passing — these do NOT appear in `findings[]`.

**N/A Handling During Parsing:**

When a question is in `evaluations[]` with status `N/A`:
- Record it as N/A for this service
- **Do NOT treat N/A as a gap** — a question that is N/A for a service does not count as a BLOCKER or RISK for that service in cross-cutting analysis
- Track which questions are N/A per service for use in cross-cutting analysis (Steps 4 and 4b)

#### 2.4 Conditional BLOCKER Tracking

For the 5 conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2), record:
- The resolved severity (BLOCKER, RISK-SAFETY, RISK-QUALITY, or INFO — depending on the service's agent_scope and, for DATA-Q1, which of the B1/B2/B3 sub-checks fired)
- The agent_scope that determined the resolution
- For DATA-Q1: which sub-checks (B1 API response scoping, B2 access control differentiation, B3 formal classification metadata) contributed to the resolved severity

This is used in cross-cutting analysis to distinguish between services where a conditional question resolved as BLOCKER vs. those where it resolved as INFO/RISK. DATA-Q1 resolves to BLOCKER, RISK-SAFETY, or INFO for data-handling applications based on which sub-checks fire — aggregation logic must treat its tiered resolutions accordingly rather than assuming any DATA-Q1 flag equals a BLOCKER.

#### 2.5 Error Handling

- Log warnings for missing sections (use defaults where possible)
- Log warnings for malformed severity values (exclude from aggregations)
- Handle duplicate service names with disambiguation using repository path
- If a report is missing the readiness profile section, attempt to derive it from blocker/risk counts. If counts are also missing, exclude the report from portfolio analysis and log a warning.

### Step 3: Build Executive Dashboard

Aggregate the parsed data into a portfolio-level executive dashboard.

#### 3.1 Readiness Distribution

Count and calculate the percentage of services in each readiness profile:

| Profile | Count | Percentage |
|---------|-------|------------|
| Agent-Ready | N | X% |
| Pilot-Ready | N | X% |
| Pilot-Ready (Safety Concerns) | N | X% |
| Remediation Required | N | X% |
| Not Agent-Integrable | N | X% |

**Calculation:**
- For each profile, count the number of services with that profile
- Percentage = (count / total services) × 100, rounded to nearest integer
- Total must equal the number of assessed services

#### 3.2 Portfolio Summary Metrics

Calculate portfolio-wide summary metrics:

| Metric | Calculation |
|--------|-------------|
| Total services assessed | Count of valid ARA reports parsed |
| Services ready for agents (Agent-Ready + Pilot-Ready) | Count and percentage |
| Total unique BLOCKERs across portfolio | Count of distinct question IDs that appear as BLOCKER in any service |
| Total unique RISKs across portfolio | Count of distinct question IDs that appear as RISK in any service |
| Cross-cutting BLOCKERs | Count of question IDs that appear as BLOCKER in 2+ services (from Step 4) |
| Cross-cutting RISKs | Count of question IDs that appear as RISK at-or-above the scaling threshold, max(3, 33% of applicable repos) (from Step 4b) |
| Services with write-enabled agent scope | Count and percentage |
| Services with read-only agent scope | Count and percentage |

#### 3.3 Repo Type Distribution

Count services by repo type:

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | N | X% |
| infrastructure-only | N | X% |
| deployment-config | N | X% |
| monorepo | N | X% |
| library | N | X% |

#### 3.4 Blocker Heatmap by Section

Aggregate BLOCKER counts by ARA section to surface which dimensions are blocking the most repos. This is the key metric for identifying platform-level investments vs. individual service fixes.

For each of the 8 ARA sections (API, AUTH, STATE, HITL, DATA, DISC, OBS, ENG):

1. Count the number of repos that have at least one BLOCKER in that section (excluding N/A questions)
2. Calculate the percentage of applicable repos blocked by that section
3. List the top blocker question IDs in that section

**Calculation:**

```
for each section in [API, AUTH, STATE, HITL, DATA, DISC, OBS, ENG]:
    repos_blocked = 0
    applicable_repos = 0
    blocker_questions = set()
    
    for each service in portfolio:
        has_applicable_question = false
        has_blocker = false
        
        for each question_id in section:
            severity = service.findings[question_id].severity
            if severity != "N/A":
                has_applicable_question = true
                if severity == "BLOCKER":
                    has_blocker = true
                    blocker_questions.add(question_id)
        
        if has_applicable_question:
            applicable_repos += 1
            if has_blocker:
                repos_blocked += 1
    
    record: section, repos_blocked, applicable_repos, percentage, top blocker_questions
```

Order sections by repos_blocked descending — the section blocking the most repos is the highest priority platform investment.

#### 3.5 Readiness Snapshot

Produce a structured, machine-parseable summary block containing the key portfolio metrics. This block is designed for consumption by dashboard and tracking systems that build time-series views across multiple analysis runs.

The snapshot captures the state of the portfolio at analysis time. Delta calculations (blockers resolved, profile changes, velocity) are the responsibility of the consuming system, not this TD.

Fields:

| Field | Type | Source |
|-------|------|--------|
| `analysis_date` | string (YYYY-MM-DD) | Report date |
| `total_services` | integer | Count of assessed services |
| `agent_ready` | integer | Count with Agent-Ready profile |
| `pilot_ready` | integer | Count with Pilot-Ready profile |
| `pilot_ready_safety_concerns` | integer | Count with Pilot-Ready (Safety Concerns) profile |
| `remediation_required` | integer | Count with Remediation Required profile |
| `not_integrable` | integer | Count with Not Agent-Integrable profile |
| `total_blockers` | integer | Sum of BLOCKER counts across all services |
| `total_risks` | integer | Sum of RISK counts across all services (RISK-SAFETY + RISK-QUALITY combined) |
| `total_risk_safety` | integer | Sum of RISK-SAFETY counts across all services |
| `total_risk_quality` | integer | Sum of RISK-QUALITY counts across all services |
| `total_infos` | integer | Sum of INFO counts across all services |
| `cross_cutting_blockers` | integer | Count of question IDs that are BLOCKER in 2+ repos |
| `cross_cutting_risks` | integer | Count of question IDs that are RISK at-or-above scaling threshold (RISK-SAFETY + RISK-QUALITY combined) |
| `cross_cutting_risk_safety` | integer | Count of RISK-SAFETY questions at-or-above scaling threshold |
| `cross_cutting_risk_quality` | integer | Count of RISK-QUALITY questions at-or-above scaling threshold |
| `portfolio_level_blockers` | integer | Count of portfolio-level questions (PORT-ARA-Q1–Q5) scored as BLOCKER |
| `portfolio_level_risks` | integer | Count of portfolio-level questions (PORT-ARA-Q1–Q5) scored as RISK |
| `write_enabled_services` | integer | Count with write-enabled agent scope |
| `read_only_services` | integer | Count with read-only agent scope |

### Step 4: Identify Cross-Cutting BLOCKERs

Identify BLOCKER questions that appear across multiple services. These represent portfolio-wide agentic readiness gaps that should be addressed with coordinated remediation.

#### 4.1 Cross-Cutting BLOCKER Identification

For each of the 43 ARA question IDs:

1. Collect the severity for that question across all services
2. **Exclude services where the question is N/A** — a question that is N/A for a service does not count as a BLOCKER for that service
3. Count the number of services where the question has severity = BLOCKER
4. **If the count is 2 or more**, flag the question as a cross-cutting BLOCKER

**Fan-in escalation rule:** Additionally, a BLOCKER in a single service is escalated to cross-cutting status (annotated as "Single-service BLOCKER with portfolio-wide blast radius") when ANY of the following are true:
- The service has fan-in ≥ 3 in `dependency_overrides` (3+ other services depend on it)
- The service is marked P0 priority in `service_inventory`
- The service is on the critical path (appears as a transitive dependency for 50%+ of the portfolio)

This ensures that a critical gateway service with a BLOCKER is not invisible simply because the gap is unique to that service.

**Algorithm:**

```
for each question_id in all_43_questions:
    blocker_services = []
    applicable_services = []
    
    for each service in portfolio:
        severity = service.findings[question_id].severity
        if severity == "N/A":
            continue  # Skip — N/A is not a gap
        applicable_services.append(service)
        if severity == "BLOCKER":
            blocker_services.append(service)
    
    if len(blocker_services) >= 2:
        flag as cross-cutting BLOCKER
        record: question_id, blocker_services, applicable_services count
```

#### 4.2 Cross-Cutting BLOCKER Output

For each cross-cutting BLOCKER, record:

- **Question ID** — e.g., AUTH-Q1
- **Question topic** — e.g., "Machine Identity Authentication"
- **Affected services** — List of service names where this is a BLOCKER
- **Applicable services** — Count of services where this question is not N/A
- **Impact** — X of Y applicable services have this BLOCKER
- **Common findings** — Summarize the findings across affected services (look for patterns)
- **Portfolio-level remediation** — A coordinated remediation recommendation that addresses all affected services (generated in Step 6)

#### 4.3 Conditional BLOCKER Handling in Cross-Cutting Analysis

For conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2):
- Only count a service as having a BLOCKER if the conditional resolved to BLOCKER for that service (i.e., agent_scope was "write-enabled" or, for DATA-Q1, B1 fired under write-enabled/data-export-enabled scope)
- Services where the conditional resolved to INFO or RISK (agent_scope was "read-only", or for DATA-Q1 only B2/B3 fired) do NOT count toward the cross-cutting BLOCKER threshold
- Count these services under the cross-cutting RISK analysis instead (Step 4b)
- Note in the output which services have write-enabled scope (and thus BLOCKER) vs. read-only scope (and thus INFO/RISK) for these questions. For DATA-Q1, also note which sub-check (B1/B2/B3) drove the resolved severity.

### Step 4b: Identify Cross-Cutting RISKs

Identify RISK questions that appear across multiple services. These represent portfolio-wide patterns that warrant coordinated attention. Cross-cutting RISKs are aggregated separately for RISK-SAFETY and RISK-QUALITY tiers.

#### 4b.1 Cross-Cutting RISK Identification

For each of the 43 ARA question IDs, determine the question's RISK tier (RISK-SAFETY or RISK-QUALITY) and run the aggregation algorithm separately per tier:

1. Determine the RISK tier for the question (RISK-SAFETY or RISK-QUALITY)
2. Collect the severity for that question across all services
3. **Exclude services where the question is N/A** — a question that is N/A for a service does not count as a RISK for that service
4. Count the number of services where the question has severity matching the specific tier (RISK-SAFETY or RISK-QUALITY)
5. **If the count meets the threshold** — max(3, 33% of applicable repos), with a floor of 2 for portfolios with fewer than 4 applicable repos — flag the question as a cross-cutting finding for that tier

**Algorithm:**

```
for each question_id in all_43_questions:
    tier = get_risk_tier(question_id)  # RISK-SAFETY or RISK-QUALITY
    
    risk_services = []
    applicable_services = []
    
    for each service in portfolio:
        severity = service.findings[question_id].severity
        if severity == "N/A":
            continue  # Skip — N/A is not a gap
        applicable_services.append(service)
        if severity == tier:  # Match the specific tier
            risk_services.append(service)
    
    risk_threshold = max(3, ceil(len(applicable_services) * 0.33))
    if len(applicable_services) < 4:
        risk_threshold = 2  # Small portfolio accommodation
    if len(risk_services) >= risk_threshold:
        flag as cross-cutting {tier} finding
        record: question_id, tier, risk_services, applicable_services count
```

**RISK-SAFETY questions (16):** AUTH-Q2, AUTH-Q3, AUTH-Q4, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q3, STATE-Q4, STATE-Q5, STATE-Q6, DATA-Q1, DATA-Q2, DATA-Q6, HITL-Q1, HITL-Q2

**RISK-QUALITY questions (17):** API-Q2, API-Q3, API-Q6, STATE-Q2, STATE-Q7, DATA-Q3, DATA-Q4, DATA-Q5, DISC-Q1, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3, ENG-Q4, ENG-Q5, HITL-Q3

Note: AUTH-Q6, STATE-Q1, DATA-Q1, and DATA-Q2 are conditional BLOCKER questions. When the conditional resolves to RISK (read-only scope, or for DATA-Q1 when only B2 fires), they resolve to RISK-SAFETY. Only count services where the resolved severity matches RISK-SAFETY for these questions.

#### 4b.2 Cross-Cutting RISK Output

Cross-cutting RISKs are split into two subsections: RISK-SAFETY findings first, then RISK-QUALITY findings.

For each cross-cutting RISK, record:

- **Question ID** — e.g., AUTH-Q2
- **Tier** — RISK-SAFETY or RISK-QUALITY
- **Question topic** — e.g., "Scoped Permissions"
- **Affected services** — List of service names where this is a RISK at the matching tier
- **Applicable services** — Count of services where this question is not N/A
- **Impact** — X of Y applicable services have this RISK
- **Common findings** — Summarize the findings across affected services
- **Portfolio-level recommendation** — A coordinated recommendation that addresses all affected services

### Step 5: Build Service Dependency Map

Construct a service dependency map using the `dependency_overrides` from `additionalPlanContext`.

#### 5.1 Dependency Graph Construction

If `dependency_overrides` is provided:

- Create a directed graph with services as nodes and dependencies as edges
- For each dependency override entry:
  - Add an edge from `source` to `target`
  - Label the edge with `type` (sync, async, shared_db, shared_infra) and `description`
- Cross-reference with discovered services — log a warning if a dependency references a service not found in the report inventory

**Dependency Types:**

| Type | Description | Implication for Agentic Readiness |
|------|-------------|-----------------------------------|
| `sync` | Synchronous REST/gRPC call | Agent calling source service may transitively depend on target service availability and auth |
| `async` | Message queue, event bus, pub/sub | Agent actions on source may trigger async effects on target — audit trail must span both |
| `shared_db` | Multiple services access same database | Agent write operations on one service may affect data visible to another — data integrity risk |
| `shared_infra` | Common API gateway, auth system, load balancer | Shared infrastructure blockers (e.g., no machine identity) affect all dependent services |

#### 5.2 Dependency Analysis

For each service, calculate:

- **Fan-in** — Count of services that depend on this service (number of edges pointing to it)
- **Fan-out** — Count of services this service depends on (number of edges pointing from it)
- **Foundation services** — Services with fan-in >= 3 AND fan-out <= 1 (many depend on them, they depend on few)
- **Leaf services** — Services with fan-in <= 1 AND fan-out >= 2 (few depend on them, they depend on many)

#### 5.3 Dependency-Aware Readiness Insights

Combine dependency information with readiness profiles to identify high-risk patterns:

- **High-risk foundation services** — Foundation services (high fan-in) with readiness profile "Remediation Required" or "Not Agent-Integrable". These are critical because many services depend on them, and their blockers may cascade.
- **Shared infrastructure blockers** — If a `shared_infra` dependency target has BLOCKERs (e.g., AUTH-Q1: no machine identity on the shared auth system), all services using that shared infrastructure are affected.
- **Transitive blocker propagation** — If Service A depends synchronously on Service B, and Service B is "Not Agent-Integrable", then Service A's agent integration is also blocked regardless of its own readiness profile.

#### 5.4 No Dependency Information

If `dependency_overrides` is not provided:

**Infer dependencies from individual ARA reports.** Rather than skipping dependency analysis entirely, extract dependency information from the individual report findings:

1. **Scan individual report findings** for evidence of inter-service communication:
   - Look for mentions of gRPC/REST calls to other services in the portfolio (e.g., "calls cartservice via gRPC", "depends on productcatalogservice")
   - Look for shared data store references (e.g., "Redis backing store shared with...")
   - Look for service names mentioned in context fields, findings, or evidence sections
   - Look for import/client references to other services in the codebase (e.g., `NewCheckoutServiceClient`, `CartServiceClient`)

2. **Construct an inferred dependency graph** using the same structure as explicit `dependency_overrides`:
   - Set `type` based on communication pattern: `sync` for REST/gRPC calls, `async` for message queue/event references, `shared_db` for shared data store references, `shared_infra` for shared infrastructure references
   - Set `description` from the evidence found in the report
   - Mark all inferred dependencies as `"inferred": true` to distinguish from explicit overrides

3. **Apply Steps 5.1–5.3 normally** using the inferred dependency graph — calculate fan-in/fan-out, identify foundation services, and perform transitive blocker propagation analysis

4. **Add a note in the service dependency map section:**

> Dependencies were inferred from individual ARA report findings (not explicitly provided via `dependency_overrides`). Inferred dependencies may be incomplete — they reflect only what was observable in the assessed code and report context. For authoritative dependency data, add `dependency_overrides` to the portfolio config.

If no dependencies can be inferred from the reports, display a note that no dependency information was available and produce the service-by-service summary without dependency enrichment.

### Step 6: Generate Portfolio-Level Remediation Guidance

For each cross-cutting BLOCKER identified in Step 4, generate coordinated remediation guidance that addresses the gap across all affected services.

#### 6.1 Remediation Guidance Structure

For each cross-cutting BLOCKER:

- **Question ID and topic** — e.g., AUTH-Q1: Machine Identity Authentication
- **Portfolio impact** — X of Y applicable services affected
- **Root cause pattern** — Identify the common root cause across affected services (e.g., "No service accounts configured — all services use shared credentials or human credentials")
- **Coordinated remediation approach** — A portfolio-level solution that addresses all affected services:
  - **Platform-level fix** — If the blocker can be resolved at the platform/infrastructure level (e.g., deploying a centralized identity provider), describe the shared solution
  - **Per-service fix** — If each service needs individual remediation, describe the common pattern and estimate effort per service
  - **Hybrid approach** — If both platform and per-service work is needed, describe the split
- **Estimated effort** — High / Medium / Low for the portfolio-level remediation
- **Priority** — Based on the number of affected services and the severity of the gap:
  - **Critical** — Affects all or nearly all services, or affects foundation services with high fan-in
  - **High** — Affects majority of services
  - **Medium** — Affects a subset of services
- **Dependencies** — Other cross-cutting BLOCKERs that should be resolved first (e.g., "Resolve AUTH-Q1 before AUTH-Q6 — you need machine identity before you can audit agent actions")

#### 6.2 Remediation Prioritization

Order the cross-cutting BLOCKERs by remediation priority:

1. **Identity and access BLOCKERs first** (AUTH section) — You cannot enforce any other security control without identity
2. **Data integrity BLOCKERs second** (STATE, DATA sections) — Protect data before enabling agent writes
3. **API surface BLOCKERs third** (API section) — Ensure stable integration surface
4. **Remaining BLOCKERs** — Ordered by number of affected services (most affected first)

If `context` was provided in additionalPlanContext, use it to tailor the remediation guidance to the portfolio's specific situation.

### Step 7: Recommend Agentic Programs

Based on the portfolio-wide analysis findings, recommend relevant agentic enablement programs and engagement workshops. The single authoritative catalog of programs is the shared **AWS Program & GTM Library** (`references/program-library.md`, shipped alongside this definition) — never expose internal numeric scores in the output.

#### 7.1 Program Catalog and Trigger Logic

Evaluate each eligible program against its trigger condition using the shared **AWS Program & GTM Library** (`references/program-library.md`) — the single authoritative catalog, shipped alongside this definition. Load that file and evaluate **every `[ARA]` and `[ARA+MOD]` program** (including the `[ARA-anchor]` programs AI DLC, AXE, and Innovation EBA) against the portfolio findings, applying each program's signal patterns, "DO NOT recommend when" exclusions, and qualification criteria. Include a program only if its signal patterns match AND none of its exclusions apply. Multiple programs can be triggered simultaneously. Follow the library's prioritization, `Funded Programs → Engagement Models` grouping, status filtering, assessment-overlap / EBA-vs-AML rules, and run its reasoning checklist before finalizing. Cap the final list at 3–5.

#### 7.2 Program Sequencing Guidance

When multiple programs are triggered, recommend them in this order:

1. **AI DLC** (if triggered) — Run first to establish AI-driven development practices before agentic work
2. **AXE** (if triggered) — Run after AI DLC to design the agent experience
3. **Innovation EBA** (if triggered) — Run when the customer is ready to accelerate an AI/ML or GenAI use case into production (can run in parallel with AXE if use cases are independent)

If only one program is triggered, recommend it directly without sequencing context.

#### 7.3 Program Recommendations Output

For each triggered program:

- **Program name** — AI DLC, AXE, or Innovation EBA
- **Relevance** — Why this program is recommended based on portfolio findings
- **Trigger findings** — Specific portfolio metrics that triggered the recommendation
- **What it provides** — Brief description of the program's value
- **Suggested timing** — When to run relative to other programs or analysis phases
- **Next step** — Recommended action (e.g., "Request engagement via AWS Solutions Architect")

If no programs are triggered, include a brief note: "No specific agentic program recommendations based on current findings. As the portfolio's agentic readiness improves, re-assess to identify program eligibility."


### Step 8: Evaluate Portfolio-Level Questions

Evaluate questions that can only be answered by looking across multiple repos. These are distinct from cross-cutting analysis (Step 4) which aggregates individual findings — portfolio-level questions assess capabilities that no individual repo analysis can see.

Individual report findings are never overridden. Where a portfolio-level finding provides context for an individual blocker, annotate it with "potentially mitigated — verify" but do not change individual counts.

#### 8.1 Portfolio-Level Questions (5)

| ID | Question | Severity | How to Evaluate |
|----|----------|----------|-----------------|
| PORT-ARA-Q1 | **Centralized Identity Plane** — Is there a shared identity provider that all services use for agent M2M authentication? | BLOCKER if no shared IdP detected across any repo; RISK if shared IdP exists but not all services are integrated | Scan all repos for Cognito User Pools, Cognito Identity Pools, Okta configs, or shared auth middleware. Check if the same IdP resource (by ARN, name, or config reference) appears in 2+ repos. Cross-reference with `shared_infra` dependencies. If a shared IdP is found in an infra repo but application repos don't reference it, score as RISK with annotation "shared IdP exists in {repo} but integration not confirmed in {services}." |
| PORT-ARA-Q2 | **Cross-Service Audit Correlation** — Can audit logs be correlated across services for end-to-end agent action tracing? | RISK if no shared trace ID propagation or centralized audit trail detected | Check for: (1) shared CloudTrail trail covering multiple services, (2) consistent trace ID headers (X-Amzn-Trace-Id, traceparent) across repos, (3) centralized log aggregation (CloudWatch Log Groups with shared retention, S3 audit bucket). If individual repos log independently with no correlation mechanism, score as RISK. |
| PORT-ARA-Q3 | **Portfolio-Level Rate Limiting** — Is there a shared API gateway or WAF protecting the portfolio perimeter from agent traffic storms? | RISK if no shared WAF or API gateway detected; INFO if each service has its own rate limiting | Check for: (1) shared WAF WebACL referenced across repos, (2) shared API Gateway with usage plans, (3) portfolio-level rate limiting rules. If rate limiting exists only at individual service level, score as INFO with note that portfolio-level protection is recommended for agent-at-scale scenarios. |
| PORT-ARA-Q4 | **Transitive Dependency Safety** — Do dependency chains create transitive agent safety risks? | BLOCKER if a service with profile Agent-Ready or Pilot-Ready depends (sync) on a service with profile Not Agent-Integrable; RISK if depends on Remediation Required | Using the dependency graph from Step 5 and readiness profiles from Step 3, trace sync dependency chains. If Service A (Agent-Ready) synchronously depends on Service B (Not Agent-Integrable), Service A's agent integration is effectively blocked regardless of its own profile. Flag as BLOCKER. Async dependencies are RISK (eventual consistency issues but not hard blocks). |
| PORT-ARA-Q5 | **Agent Identity Governance** — Is there a centralized mechanism to suspend or revoke agent identities across all services simultaneously? | RISK if no portfolio-wide agent identity registry or centralized revocation mechanism detected | Check for: (1) shared Cognito app client registry, (2) centralized API key management, (3) portfolio-level agent identity documentation. If each service manages agent identities independently with no centralized kill switch, score as RISK. |

#### 8.2 Contextual Annotations

When a portfolio-level finding provides context for individual cross-cutting BLOCKERs, add an annotation to the cross-cutting BLOCKER section:

```markdown
> **Portfolio Context**: <portfolio-level question ID> found that <finding>.
> This may mitigate this blocker for <services> — **verify** that <specific check>.
```

Example:
```markdown
> **Portfolio Context**: PORT-ARA-Q1 found a shared Cognito User Pool in eks-saas-gitops
> (terraform/cognito.tf). This may mitigate AUTH-Q1 for services deployed on this
> cluster — **verify** that each service's API Gateway has a Cognito authorizer attached.
```

Do NOT change individual blocker counts or readiness profiles based on portfolio-level findings. The annotation is informational — human verification is required.

#### 8.3 Portfolio-Level Findings Output

Record portfolio-level question results in a dedicated section of the report, separate from cross-cutting analysis. Include:

- **Question ID and topic**
- **Severity** (BLOCKER / RISK / INFO)
- **Finding** — what was observed across the portfolio
- **Evidence** — specific repos, files, or configurations that informed the finding
- **Recommendation** — portfolio-level action to address the gap
- **Affected Services** — which services are impacted
- **Contextual Annotations** — any individual blockers this finding provides context for



## Reference Files

This definition is split into a lean orchestration spine (this file) plus reference files, loaded on demand at the point in the flow where each is needed. Load each file when the step below directs you to — do not skip any.

- **`references/program-library.md`** — the shared, authoritative AWS Program & GTM Library. Loaded in Step 7 to recommend agentic enablement programs. This file is shipped identically alongside the portfolio-mod TD.
- **`references/01-report-template.md`** — the markdown report structure: executive dashboard, cross-cutting BLOCKERs/RISKs, dependency map, remediation guidance, program recommendations, portfolio-level findings, service-by-service summary, analysis inventory.
- **`references/02-output-contract.md`** — the machine-readable four-artifact contract: top-level JSON keys, remediation roadmap, recommended actions, HTML visual contract, and error handling.


## Report Template

After completing the analysis steps, compile the aggregated findings into the four-artifact bundle. The full markdown report structure is in **`references/01-report-template.md`** — load that file and follow it exactly. The JSON and HTML artifacts render subsets of the same data per the Output Contract.

## Constraints and Guardrails

Strictly follow these rules at all times:

- **Read-only analysis**: Do not modify any source code, configuration, or infrastructure. Only create the output portfolio artifact bundle (MD, JSON, HTML, and metadata.json).
- **Stay on the current branch**: This is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out and perform all work there.
- **Minimum 2 reports**: The portfolio analysis requires at least 2 valid ARA reports. Terminate with a clear error if fewer than 2 are found.
- **N/A exclusion**: Questions scored as N/A for a service do NOT count as gaps for that service in cross-cutting analysis. A question that is N/A for a service is excluded from BLOCKER and RISK counts for cross-cutting identification.
- **Cross-cutting thresholds**: BLOCKERs require 2+ repos. RISKs require max(3, 33% of applicable repos) with a floor of 2 for portfolios with fewer than 4 applicable repos. Do not lower these thresholds.
- **Evidence-based**: All cross-cutting findings must reference specific question IDs and service names. Do not make vague claims — state which services are affected and which questions triggered the finding.
- **Conditional BLOCKER accuracy**: When counting cross-cutting BLOCKERs for conditional questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2), only count services where the conditional resolved to BLOCKER (write-enabled scope, or for DATA-Q1 when B1 fires under write-enabled scope). Do not count services where it resolved to INFO/RISK (read-only scope, or for DATA-Q1 when only B2/B3 fired).
- **Report completeness**: The output report must contain all required sections: executive dashboard, cross-cutting BLOCKERs, cross-cutting RISKs, service dependency map, remediation guidance, agentic program recommendations, portfolio-level findings (PORT-ARA-Q1 through PORT-ARA-Q5), service-by-service summary, and analysis inventory.

## Output Contract

Emit the four-artifact bundle exactly as specified in **`references/02-output-contract.md`**: the four-artifact contract, top-level JSON keys, remediation roadmap, recommended actions, HTML visual contract, and error handling. Load that file and conform to it — it is the machine-readable contract the webapp and portfolio aggregator consume.
