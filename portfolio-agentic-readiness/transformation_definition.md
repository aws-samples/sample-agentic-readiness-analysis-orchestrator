## Name

Portfolio Agentic Readiness Assessment

## Objective

Aggregate individual repository Agentic Readiness Assessment (ARA) reports into a portfolio-level analysis that identifies cross-cutting blockers, shared risks, service dependency patterns, and portfolio-wide remediation guidance — enabling coordinated agentic readiness across the entire service estate.

## Summary

This transformation consumes multiple individual ARA reports (`*-ara-report.md` files) from different repositories and produces a comprehensive portfolio-level view focused exclusively on agentic readiness. It performs intelligent discovery and parsing of ARA reports, identifies cross-cutting BLOCKERs and RISKs that appear across multiple services, constructs a service dependency map from portfolio configuration, generates portfolio-level remediation guidance, recommends agentic enablement programs, and produces a service-by-service summary.

The transformation follows a 7-step pipeline:
1. **Read Context**: Parse additionalPlanContext for portfolio framing
2. **Discovery**: Locate all ARA report files in the directory structure
3. **Parsing**: Extract readiness profiles, severity counts, and per-question findings from each report
4. **Executive Dashboard**: Build readiness distribution across the portfolio
5. **Cross-Cutting Analysis**: Identify BLOCKERs appearing in 2+ repos and RISKs appearing in 3+ repos
6. **Dependency Mapping**: Construct service dependency map from dependency_overrides
7. **Recommendations**: Generate remediation guidance and agentic program recommendations

The output is a detailed Markdown report saved as `portfolio-ara-report.md` containing:
- Executive dashboard with readiness distribution by profile
- Blocker heatmap by section (which dimensions block the most repos)
- Readiness snapshot (structured, machine-parseable metrics for dashboard consumption)
- Cross-cutting BLOCKERs (same blocker question in 2+ repos)
- Cross-cutting RISKs (same risk question in 3+ repos)
- Service dependency map from dependency_overrides
- Portfolio-level remediation guidance for cross-cutting blockers
- Agentic program recommendations (EBA-Agentic AI)
- Service-by-service summary (repo name, profile, blocker count, risk count)

This portfolio TD does **NOT** include:
- Modernization pathways
- Roadmap phases
- Numeric scores or score averages
- Tiered gap classification
- Goal-based re-weighting
- Technology preferences
- Quick Agent Wins aggregation
- Resource allocation recommendations

## Entry Criteria

- At least 2 individual ARA reports exist in repository directories
- ARA reports follow the expected structure: readiness profile, BLOCKER/RISK/INFO counts, detailed findings for 49 questions
- Reports are accessible at specified paths or in a common directory structure
- Write permissions exist to create the output directory and portfolio report file

## Implementation Steps

### Step 0: Read additionalPlanContext

Before beginning discovery, read the portfolio assessment context from `additionalPlanContext` to extract framing information and service configuration.

#### 0.1 Read Portfolio Context

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
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

#### 0.3 Fields NOT Read by This TD

The Portfolio ARA TD does **not** read, validate, or apply the following fields from `additionalPlanContext`. If present, they are ignored:

- **`preferences`** — The `preferences` field (prefer/avoid arrays) is a MOD-only concept used for technology recommendation steering. The Portfolio ARA TD evaluates agentic readiness patterns — it does not make technology recommendations.
- **`agent_scope`** — Agent scope is a per-repo field consumed by individual ARA TDs. The portfolio TD reads agent_scope from individual report metadata, not from its own additionalPlanContext.
- **`goal`** — There is no goal system. The Portfolio ARA TD operates without goal-based re-weighting, conditional sections, or phase naming.
- **`goal_context`** — Replaced by the `context` field.


### Step 1: Discovery — Locate ARA Reports

Scan the target directory structure to find all individual ARA reports.

#### 1.1 Discovery Process

- Recursively search for files matching the pattern `*-ara-report.md` in the directory tree
- For each report found, extract the project/service name from the filename (the prefix before `-ara-report.md`)
- Extract the repository path (parent directory or grandparent directory of the report file)
- Create an inventory of all services assessed with their report file locations
- Validate minimum requirement: at least 2 reports must be discovered

**Input Options:**
- A parent directory containing multiple repository folders, each with an ARA report, OR
- A list of explicit paths to ARA report files (from `service_inventory` paths)

#### 1.2 Validation

- Verify each discovered file exists and is readable
- Verify each file follows the expected ARA report structure:
  - Contains a "Readiness Profile" section
  - Contains BLOCKER/RISK/INFO summary counts
  - Contains detailed findings with question IDs (API-Q1 through ENG-Q6)
- Exclude files that don't match the expected ARA report structure — log a warning for each excluded file
- Log warnings for inaccessible or malformed files
- **Terminate with a clear error if fewer than 2 valid ARA reports are found**

#### 1.3 Build Report Inventory

After discovery, compile a structured inventory:

| Field | Source |
|-------|--------|
| Service name | Extracted from filename prefix |
| Report file path | Full path to the `*-ara-report.md` file |
| Repository path | Parent directory of the report |
| Priority | From `service_inventory` if available, otherwise not set |
| Repo type | Extracted from report metadata header |
| Agent scope | Extracted from report metadata header |

Cross-reference discovered reports with `service_inventory` (if provided) to enrich metadata. If a service appears in `service_inventory` but no report is found, log a warning: "Service '{name}' listed in service_inventory but no ARA report found at expected path."

### Step 2: Parse Individual ARA Reports

For each ARA report found, extract the data needed for portfolio-level analysis.

#### 2.1 Service Metadata

Extract from the report metadata header:

- **Service/repository name** — from the report header or filename
- **Assessment date** — from the report metadata (validate YYYY-MM-DD format)
- **Repo type** — from the metadata line `**Repository Type**: <value>` (e.g., `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`). If absent, assume `application`.
- **Agent scope** — from the metadata line `**Agent Scope**: <value>` (e.g., `read-only`, `write-enabled`). If absent, assume `read-only`.

#### 2.2 Readiness Profile

Extract the readiness profile from the "Readiness Profile" section:

- **Profile** — One of: `Agent-Ready`, `Pilot-Ready`, `Remediation Required`, `Not Agent-Integrable`
- **Blocker count** — Number of BLOCKERs (excluding N/A)
- **Risk count** — Number of RISKs (excluding N/A)
- **Info count** — Number of INFOs (excluding N/A)
- **N/A count** — Number of questions scored as N/A

#### 2.3 Detailed Findings (Per-Question)

For each of the 49 questions (API-Q1 through ENG-Q6), extract:

- **Question ID** — e.g., API-Q1, AUTH-Q7, ENG-Q3
- **Severity** — BLOCKER, RISK, INFO, or N/A
- **Finding** — What was observed
- **Gap** — What is missing (or N/A)
- **Recommendation** — What to do (or N/A)

**N/A Handling During Parsing:**

When a question has severity N/A:
- Record it as N/A in the parsed data
- **Do NOT treat N/A as a gap** — a question that is N/A for a service does not count as a BLOCKER or RISK for that service in cross-cutting analysis
- Track which questions are N/A per service for use in cross-cutting analysis (Steps 3 and 4)

#### 2.4 Conditional BLOCKER Tracking

For the 4 conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q7, DATA-Q2), record:
- The resolved severity (BLOCKER, RISK, or INFO — depending on the service's agent_scope)
- The agent_scope that determined the resolution

This is used in cross-cutting analysis to distinguish between services where a conditional question resolved as BLOCKER vs. those where it resolved as INFO/RISK.

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
| Cross-cutting RISKs | Count of question IDs that appear as RISK in 3+ services (from Step 4) |
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

Produce a structured, machine-parseable summary block containing the key portfolio metrics. This block is designed for consumption by dashboard and tracking systems that build time-series views across multiple assessment runs.

The snapshot captures the state of the portfolio at assessment time. Delta calculations (blockers resolved, profile changes, velocity) are the responsibility of the consuming system, not this TD.

Fields:

| Field | Type | Source |
|-------|------|--------|
| `assessment_date` | string (YYYY-MM-DD) | Report date |
| `total_services` | integer | Count of assessed services |
| `agent_ready` | integer | Count with Agent-Ready profile |
| `pilot_ready` | integer | Count with Pilot-Ready profile |
| `remediation_required` | integer | Count with Remediation Required profile |
| `not_integrable` | integer | Count with Not Agent-Integrable profile |
| `total_blockers` | integer | Sum of BLOCKER counts across all services |
| `total_risks` | integer | Sum of RISK counts across all services |
| `total_infos` | integer | Sum of INFO counts across all services |
| `cross_cutting_blockers` | integer | Count of question IDs that are BLOCKER in 2+ repos |
| `cross_cutting_risks` | integer | Count of question IDs that are RISK in 3+ repos |
| `portfolio_level_blockers` | integer | Count of portfolio-level questions (PORT-ARA-Q1–Q5) scored as BLOCKER |
| `portfolio_level_risks` | integer | Count of portfolio-level questions (PORT-ARA-Q1–Q5) scored as RISK |
| `write_enabled_services` | integer | Count with write-enabled agent scope |
| `read_only_services` | integer | Count with read-only agent scope |

### Step 4: Identify Cross-Cutting BLOCKERs

Identify BLOCKER questions that appear across multiple services. These represent portfolio-wide agentic readiness gaps that should be addressed with coordinated remediation.

#### 4.1 Cross-Cutting BLOCKER Identification

For each of the 49 ARA question IDs:

1. Collect the severity for that question across all services
2. **Exclude services where the question is N/A** — a question that is N/A for a service does not count as a BLOCKER for that service
3. Count the number of services where the question has severity = BLOCKER
4. **If the count is 2 or more**, flag the question as a cross-cutting BLOCKER

**Algorithm:**

```
for each question_id in all_49_questions:
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

For conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q7, DATA-Q2):
- Only count a service as having a BLOCKER if the conditional resolved to BLOCKER for that service (i.e., agent_scope was "write-enabled")
- Services where the conditional resolved to INFO or RISK (agent_scope was "read-only") do NOT count toward the cross-cutting BLOCKER threshold
- Note in the output which services have write-enabled scope (and thus BLOCKER) vs. read-only scope (and thus INFO/RISK) for these questions

### Step 4b: Identify Cross-Cutting RISKs

Identify RISK questions that appear across multiple services. These represent portfolio-wide patterns that warrant coordinated attention.

#### 4b.1 Cross-Cutting RISK Identification

For each of the 49 ARA question IDs:

1. Collect the severity for that question across all services
2. **Exclude services where the question is N/A** — a question that is N/A for a service does not count as a RISK for that service
3. Count the number of services where the question has severity = RISK
4. **If the count is 3 or more**, flag the question as a cross-cutting RISK

**Algorithm:**

```
for each question_id in all_49_questions:
    risk_services = []
    applicable_services = []
    
    for each service in portfolio:
        severity = service.findings[question_id].severity
        if severity == "N/A":
            continue  # Skip — N/A is not a gap
        applicable_services.append(service)
        if severity == "RISK":
            risk_services.append(service)
    
    if len(risk_services) >= 3:
        flag as cross-cutting RISK
        record: question_id, risk_services, applicable_services count
```

#### 4b.2 Cross-Cutting RISK Output

For each cross-cutting RISK, record:

- **Question ID** — e.g., API-Q2
- **Question topic** — e.g., "Machine-Readable API Specification"
- **Affected services** — List of service names where this is a RISK
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

If no dependencies can be inferred from the reports, fall back to the current behavior: display a note that no dependency information was available and produce the service-by-service summary without dependency enrichment.

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
- **Dependencies** — Other cross-cutting BLOCKERs that should be resolved first (e.g., "Resolve AUTH-Q1 before AUTH-Q7 — you need machine identity before you can audit agent actions")

#### 6.2 Remediation Prioritization

Order the cross-cutting BLOCKERs by remediation priority:

1. **Identity and access BLOCKERs first** (AUTH section) — You cannot enforce any other security control without identity
2. **Data integrity BLOCKERs second** (STATE, DATA sections) — Protect data before enabling agent writes
3. **API surface BLOCKERs third** (API section) — Ensure stable integration surface
4. **Remaining BLOCKERs** — Ordered by number of affected services (most affected first)

If `context` was provided in additionalPlanContext, use it to tailor the remediation guidance to the portfolio's specific situation.

### Step 7: Recommend Agentic Programs

Based on the portfolio-wide assessment findings, recommend relevant agentic enablement programs.

#### 7.1 Program Catalog and Trigger Logic

Evaluate each program against its trigger condition. Include a program in the recommendations only if its trigger condition is met.

| Program | Trigger Condition | How to Evaluate |
|---------|-------------------|-----------------|
| **EBA-Agentic AI** (Experience-Based Acceleration for Agentic AI) | Portfolio has services with readiness profile "Pilot-Ready" or "Agent-Ready" — there are services ready to begin agent integration with guided acceleration | Count services with profile Agent-Ready or Pilot-Ready. If count >= 1, recommend EBA-Agentic AI. |

#### 7.2 Program Recommendations Output

For each triggered program:

- **Program name** — e.g., EBA-Agentic AI
- **Relevance** — Why this program is recommended based on portfolio findings
- **Trigger findings** — Specific portfolio metrics that triggered the recommendation (e.g., "3 of 5 services are Pilot-Ready")
- **What it provides** — Brief description of the program's value
- **Next step** — Recommended action (e.g., "Request EBA engagement via AWS Solutions Architect")

If no programs are triggered, include a brief note: "No specific agentic program recommendations based on current findings. As the portfolio's agentic readiness improves, re-assess to identify program eligibility."


### Step 8: Evaluate Portfolio-Level Questions

Evaluate questions that can only be answered by looking across multiple repos. These are distinct from cross-cutting analysis (Step 4) which aggregates individual findings — portfolio-level questions assess capabilities that no individual repo assessment can see.

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


## Report Template

The portfolio ARA report is saved as `portfolio-ara-report.md`. The complete report structure is defined below.

---

### Report Header

```markdown
# Portfolio Agentic Readiness Assessment Report

**Date**: <YYYY-MM-DD>
**Services Assessed**: <count>
**Portfolio Context**: <context from additionalPlanContext, or "Not provided">
```

---

### Executive Dashboard

```markdown
## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | N | X% | 0 blockers, 0–2 risks — broad agent deployment |
| 🟡 Pilot-Ready | N | X% | 0 blockers, 3–5 risks — narrow pilot only |
| 🟠 Remediation Required | N | X% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | N | X% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Assessed | N |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | N (X%) |
| Services Requiring Remediation | N (X%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | N |
| Cross-Cutting RISKs (same risk in 3+ repos) | N |
| Services with Write-Enabled Agent Scope | N (X%) |
| Services with Read-Only Agent Scope | N (X%) |

### Repo Type Distribution

| Repo Type | Count | Percentage |
|-----------|-------|------------|
| application | N | X% |
| infrastructure-only | N | X% |
| deployment-config | N | X% |
| monorepo | N | X% |
| library | N | X% |

### Blocker Heatmap by Section

| Section | Repos Blocked | % of Applicable Repos | Top Blockers |
|---------|--------------|----------------------|--------------|
| <section> | N | X% | <question IDs> |
| <repeat for each of the 8 sections, ordered by repos blocked descending> |

### Readiness Snapshot

| Metric | Value |
|--------|-------|
| assessment_date | <YYYY-MM-DD> |
| total_services | <N> |
| agent_ready | <N> |
| pilot_ready | <N> |
| remediation_required | <N> |
| not_integrable | <N> |
| total_blockers | <N> |
| total_risks | <N> |
| total_infos | <N> |
| cross_cutting_blockers | <N> |
| cross_cutting_risks | <N> |
| portfolio_level_blockers | <N> |
| portfolio_level_risks | <N> |
| write_enabled_services | <N> |
| read_only_services | <N> |
```

---

### Cross-Cutting BLOCKERs

```markdown
## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

> These are BLOCKER-severity questions that appear in 2 or more repositories.
> They represent portfolio-wide agentic readiness gaps requiring coordinated remediation.
> Questions scored as N/A for a service do not count as gaps for that service.

### <question_id>: <question topic>

- **Severity**: BLOCKER in <N> of <M applicable> services
- **Affected Services**: <comma-separated service names>
- **Common Finding**: <summarized finding pattern across affected services>
- **Root Cause Pattern**: <common root cause identified across services>
- **Portfolio-Level Remediation**:
  - **Approach**: <platform-level fix, per-service fix, or hybrid>
  - **Immediate Action**: <first concrete step>
  - **Target State**: <what "resolved" looks like across the portfolio>
  - **Estimated Effort**: High / Medium / Low
  - **Priority**: Critical / High / Medium
  - **Dependencies**: <other cross-cutting BLOCKERs to resolve first, or "None">

<Repeat for each cross-cutting BLOCKER, ordered by remediation priority:
1. Identity/access BLOCKERs (AUTH section) first
2. Data integrity BLOCKERs (STATE, DATA sections) second
3. API surface BLOCKERs (API section) third
4. Remaining BLOCKERs by number of affected services>
```

If no cross-cutting BLOCKERs are identified:

```markdown
## Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos

No BLOCKER-severity questions appear in 2 or more repositories. Individual service BLOCKERs (if any) are listed in the service-by-service summary below.
```

---

### Cross-Cutting RISKs

```markdown
## Cross-Cutting RISKs — Same Risk in 3+ Repos

> These are RISK-severity questions that appear in 3 or more repositories.
> They represent portfolio-wide patterns warranting coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

### <question_id>: <question topic>

- **Severity**: RISK in <N> of <M applicable> services
- **Affected Services**: <comma-separated service names>
- **Common Finding**: <summarized finding pattern across affected services>
- **Compensating Controls**: <portfolio-level compensating controls that can be applied across services>
- **Portfolio-Level Recommendation**: <coordinated recommendation addressing all affected services>
- **Estimated Effort**: High / Medium / Low

<Repeat for each cross-cutting RISK, ordered by number of affected services (most affected first).>
```

If no cross-cutting RISKs are identified:

```markdown
## Cross-Cutting RISKs — Same Risk in 3+ Repos

No RISK-severity questions appear in 3 or more repositories. Individual service RISKs are listed in the service-by-service summary below.
```

---

### Service Dependency Map

```markdown
## Service Dependency Map

<If dependency_overrides were provided:>

### Dependency Overview

| Source Service | Target Service | Type | Description |
|---------------|---------------|------|-------------|
| <source> | <target> | sync / async / shared_db / shared_infra | <description> |
| <repeat for each dependency> |

### Service Dependency Metrics

| Service | Fan-In | Fan-Out | Role | Readiness Profile |
|---------|--------|---------|------|-------------------|
| <service name> | N | N | Foundation / Leaf / Internal | <profile> |
| <repeat for each service> |

### High-Risk Dependency Patterns

<List dependency-aware readiness insights:>

1. **<pattern name>**: <description>
   - **Affected Services**: <list>
   - **Risk**: <explain the risk>
   - **Recommendation**: <what to do>

<If no dependency_overrides were provided:>

> No dependency information was provided in the portfolio configuration. To enable
> dependency-aware analysis — including identification of high-risk foundation services,
> transitive blocker propagation, and shared infrastructure impacts — add
> `dependency_overrides` to the portfolio config.
```

---

### Remediation Guidance

```markdown
## Portfolio Remediation Guidance

<If context was provided, frame the guidance:>
> Portfolio context: <context from additionalPlanContext>

### Remediation Priority Order

Remediation of cross-cutting BLOCKERs should follow this general priority:

1. **Identity and Access** — Resolve AUTH-section BLOCKERs first. You cannot enforce any other security control without machine identity and scoped permissions.
2. **Data Integrity** — Resolve STATE and DATA-section BLOCKERs second. Protect data before enabling agent write operations.
3. **API Surface** — Resolve API-section BLOCKERs third. Ensure a stable, documented integration surface for agent tools.
4. **Remaining BLOCKERs** — Address in order of affected service count (most affected first).

### Coordinated Remediation Plan

<For each cross-cutting BLOCKER, summarize the remediation approach from Step 6.
Group related BLOCKERs that can be addressed together.>

#### <Group name — e.g., "Identity Foundation">

**BLOCKERs addressed**: <question IDs>
**Services affected**: <service names>

- **What to do**: <coordinated remediation steps>
- **Expected outcome**: <what changes when this is resolved>
- **Effort**: High / Medium / Low

<Repeat for each remediation group.>
```

---

### Agentic Programs

```markdown
## Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Next Step |
|---------|-----------|-----------------|-----------|
| <Program name> | <Why recommended> | <Specific metrics that triggered this> | <Recommended action> |
| <repeat for each triggered program> |

<If no programs are triggered:>
> No specific agentic program recommendations based on current findings. As the
> portfolio's agentic readiness improves, re-assess to identify program eligibility.

### Program Details

<For each recommended program, provide a brief paragraph:>

#### <Program Name>

<Why this program was recommended, what it provides, and suggested timing.>
```

---

### Portfolio-Level Findings

```markdown
## Portfolio-Level Findings

> These questions evaluate capabilities that can only be assessed by looking across
> multiple repos. They are distinct from cross-cutting analysis (which aggregates
> individual findings). Individual report findings are never overridden.

### <question_id>: <question topic>

- **Severity**: BLOCKER / RISK / INFO
- **Finding**: <what was observed across the portfolio>
- **Evidence**: <specific repos, files, or configurations>
- **Recommendation**: <portfolio-level action>
- **Affected Services**: <which services are impacted>
- **Contextual Annotations**: <any individual blockers this provides context for, with "verify" instructions>

<Repeat for each of the 5 portfolio-level questions (PORT-ARA-Q1 through PORT-ARA-Q5).>
```

---

### Service-by-Service Summary

```markdown
## Service-by-Service Summary

| Service | Repo Type | Agent Scope | Readiness Profile | BLOCKERs | RISKs | INFOs | N/A |
|---------|-----------|-------------|-------------------|----------|-------|-------|-----|
| <service name> | <repo_type> | <agent_scope> | <profile> | N | N | N | N |
| <repeat for each service> |

### Individual Service Details

#### <Service Name>

- **Readiness Profile**: <profile>
- **Repo Type**: <repo_type>
- **Agent Scope**: <agent_scope>
- **Priority**: <P0/P1/P2 or "Not set">
- **BLOCKERs** (N):
  - <question_id>: <brief finding summary>
  - <repeat for each BLOCKER>
- **RISKs** (N):
  - <question_id>: <brief finding summary>
  - <repeat for each RISK>
- **Key Recommendations**:
  - <top 1-3 recommendations for this service>

<If dependency information is available:>
- **Depends On**: <list of services this service depends on>
- **Depended On By**: <list of services that depend on this service>

<Repeat for each service, ordered by: Readiness Profile severity (Not Agent-Integrable first, then Remediation Required, then Pilot-Ready, then Agent-Ready), then by priority (P0 first).>
```

---

### Assessment Inventory

```markdown
## Assessment Inventory

| # | Service | Report File | Assessment Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | <service name> | <file path> | <date> | <repo_type> | <agent_scope> |
| <repeat for each service> |
```

---

### Table of Contents

The complete report structure, for reference:

```markdown
# Portfolio Agentic Readiness Assessment Report

1. Executive Dashboard
   - Readiness Distribution
   - Portfolio Summary
   - Repo Type Distribution
   - Blocker Heatmap by Section
   - Readiness Snapshot
2. Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos
3. Cross-Cutting RISKs — Same Risk in 3+ Repos
4. Service Dependency Map
5. Portfolio Remediation Guidance
6. Agentic Program Recommendations
7. Portfolio-Level Findings
8. Service-by-Service Summary
9. Assessment Inventory
```

## Constraints and Guardrails

Strictly follow these rules at all times:

- **Read-only assessment**: Do not modify any source code, configuration, or infrastructure. Only create the output portfolio report file.
- **Minimum 2 reports**: The portfolio assessment requires at least 2 valid ARA reports. Terminate with a clear error if fewer than 2 are found.
- **N/A exclusion**: Questions scored as N/A for a service do NOT count as gaps for that service in cross-cutting analysis. A question that is N/A for a service is excluded from BLOCKER and RISK counts for cross-cutting identification.
- **Cross-cutting thresholds**: BLOCKERs require 2+ repos. RISKs require 3+ repos. Do not lower these thresholds.
- **No pathways**: This portfolio TD does not include AWS Modernization Pathways, pathway aggregation, or pathway-to-learning-materials mapping. Pathways belong in the Portfolio MOD TD.
- **No roadmap phases**: This portfolio TD does not include phased roadmaps, phase assignment algorithms, or timeline estimates. Roadmaps belong in the Portfolio MOD TD.
- **No numeric scores**: This portfolio TD does not calculate numeric score averages, category scores, or overall portfolio scores. The ARA assessment uses BLOCKER/RISK/INFO severity, not numeric scales.
- **No tiered gap classification**: This portfolio TD does not use the 4-tier gap classification (Foundational Blockers, Prerequisites, Goal Deliverables, Improvement Opportunities). That classification is goal-dependent and belongs in the v1 portfolio TD. The v2 Portfolio ARA TD uses simple cross-cutting BLOCKER/RISK identification.
- **No goal system**: This TD does not read, validate, or apply any goal field. There is no goal-based re-weighting, conditional sections, or phase naming. The `context` field is used for free-text framing only.
- **No preferences**: This TD does not read or apply technology preferences (prefer/avoid arrays). Preferences are a MOD-only concept.
- **No agent_scope at portfolio level**: Agent scope is a per-repo field. The portfolio TD reads agent_scope from individual report metadata, not from its own additionalPlanContext.
- **Evidence-based**: All cross-cutting findings must reference specific question IDs and service names. Do not make vague claims — state which services are affected and which questions triggered the finding.
- **Conditional BLOCKER accuracy**: When counting cross-cutting BLOCKERs for conditional questions (API-Q4, STATE-Q1, AUTH-Q7, DATA-Q2), only count services where the conditional resolved to BLOCKER (write-enabled scope). Do not count services where it resolved to INFO/RISK (read-only scope).
- **Report completeness**: The output report must contain all required sections: executive dashboard, cross-cutting BLOCKERs, cross-cutting RISKs, service dependency map, remediation guidance, agentic program recommendations, service-by-service summary, and assessment inventory.
