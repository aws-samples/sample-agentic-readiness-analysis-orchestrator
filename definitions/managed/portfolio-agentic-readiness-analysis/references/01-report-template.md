# Portfolio ARA Report Template

> **Purpose:** Loaded by the Portfolio Agentic Readiness Analysis (portfolio-ara) TD when compiling the aggregated findings into the markdown report artifact. Defines the report header, executive dashboard, cross-cutting BLOCKERs/RISKs, service dependency map, remediation guidance, program recommendations, portfolio-level findings, service-by-service summary, analysis inventory, and table of contents.

---

## Report Template

The portfolio ARA TD emits a **four-artifact bundle**: `{portfolio_name}-portfolio-ara-report.md` (narrative), `.json` (canonical), `.html` (self-contained), `.metadata.json` (sidecar). This section specifies the MD structure; the JSON and HTML render subsets of the same data.

---

### Report Header

```markdown
# Portfolio Agentic Readiness Analysis Report

**Date**: <YYYY-MM-DD>
**Services Analyzed**: <count>
**Portfolio Context**: <context from additionalPlanContext, or "Not provided">
```

---

### Executive Dashboard

```markdown
## Executive Dashboard

### Readiness Distribution

| Profile | Services | Percentage | Description |
|---------|----------|------------|-------------|
| ✅ Agent-Ready | N | X% | 0 blockers, 0 RISK-SAFETY — broad agent deployment |
| 🟡 Pilot-Ready | N | X% | 0 blockers, 1–2 RISK-SAFETY — narrow pilot |
| 🟡 Pilot-Ready (Safety Concerns) | N | X% | 0 blockers, 3+ RISK-SAFETY — supervised pilot, prioritize safety |
| 🟠 Remediation Required | N | X% | 1–2 blockers — remediate before any agent deployment |
| ❌ Not Agent-Integrable | N | X% | 3+ blockers — deferred or descoped |

### Portfolio Summary

| Metric | Value |
|--------|-------|
| Total Services Analyzed | N |
| Services Ready for Agents (Agent-Ready + Pilot-Ready) | N (X%) |
| Services Requiring Remediation | N (X%) |
| Cross-Cutting BLOCKERs (same blocker in 2+ repos) | N |
| Cross-Cutting RISKs (same risk at-or-above scaling threshold) | N |
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
| analysis_date | <YYYY-MM-DD> |
| total_services | <N> |
| agent_ready | <N> |
| pilot_ready | <N> |
| pilot_ready_safety_concerns | <N> |
| remediation_required | <N> |
| not_integrable | <N> |
| total_blockers | <N> |
| total_risks | <N> |
| total_risk_safety | <N> |
| total_risk_quality | <N> |
| total_infos | <N> |
| cross_cutting_blockers | <N> |
| cross_cutting_risks | <N> |
| cross_cutting_risk_safety | <N> |
| cross_cutting_risk_quality | <N> |
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
- **Cross-cutting basis**: <"BLOCKER in 2+ repos" OR "Single-service BLOCKER with portfolio-wide blast radius (fan-in ≥ 3 / P0 priority / critical path)" — populate only when escalation rule applies>
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
## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Recurring Safety Risks Across Portfolio

> These are RISK-SAFETY questions that appear in at least **max(3, 33% of applicable repos)** (floor of 2 for portfolios with fewer than 4 applicable repos for the question).
> They represent portfolio-wide agent safety gaps requiring coordinated attention.
> Questions scored as N/A for a service do not count as gaps for that service.

#### <question_id>: <question topic>

- **Severity**: RISK-SAFETY in <N> of <M applicable> services
- **Affected Services**: <comma-separated service names>
- **Common Finding**: <summarized finding pattern across affected services>
- **Compensating Controls**: <portfolio-level compensating controls that can be applied across services>
- **Portfolio-Level Recommendation**: <coordinated recommendation addressing all affected services>
- **Estimated Effort**: High / Medium / Low

<Repeat for each cross-cutting RISK-SAFETY, ordered by number of affected services (most affected first).>

<If no cross-cutting RISK-SAFETY findings are identified:>

No RISK-SAFETY questions meet the cross-cutting scaling threshold.

### Cross-Cutting RISK-QUALITY — Recurring Quality Risks Across Portfolio

> These are RISK-QUALITY questions that appear in at least **max(3, 33% of applicable repos)** (floor of 2 for portfolios with fewer than 4 applicable repos for the question).
> They represent portfolio-wide quality patterns to address as capacity allows.
> Questions scored as N/A for a service do not count as gaps for that service.

#### <question_id>: <question topic>

- **Severity**: RISK-QUALITY in <N> of <M applicable> services
- **Affected Services**: <comma-separated service names>
- **Common Finding**: <summarized finding pattern across affected services>
- **Compensating Controls**: <portfolio-level compensating controls that can be applied across services>
- **Portfolio-Level Recommendation**: <coordinated recommendation addressing all affected services>
- **Estimated Effort**: High / Medium / Low

<Repeat for each cross-cutting RISK-QUALITY, ordered by number of affected services (most affected first).>

<If no cross-cutting RISK-QUALITY findings are identified:>

No RISK-QUALITY questions meet the cross-cutting scaling threshold.
```

If no cross-cutting RISKs are identified in either tier:

```markdown
## Cross-Cutting RISKs

### Cross-Cutting RISK-SAFETY — Recurring Safety Risks Across Portfolio

No RISK-SAFETY questions meet the cross-cutting scaling threshold.

### Cross-Cutting RISK-QUALITY — Recurring Quality Risks Across Portfolio

No RISK-QUALITY questions meet the cross-cutting scaling threshold. Individual service RISKs are listed in the service-by-service summary below.
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
## Recommended Actions

### Agentic Program Recommendations

> These are engagement-level recommendations based on the portfolio's agentic readiness
> profile. Discuss with your AWS Solutions Architect to determine eligibility and timing.

| Program | Relevance | Trigger Findings | Suggested Timing | Next Step |
|---------|-----------|-----------------|------------------|-----------|
| <Program name> | <Why recommended> | <Specific metrics> | <When to run> | <Action> |
| <repeat for each triggered program> |

### Program Details

#### <Program Name>

- **Why triggered**: <Portfolio metrics that triggered this recommendation>
- **What it provides**: <Brief description of the program's value>
- **Suggested timing**: <When to run relative to other programs>
- **Recommended scope**: <Which services or areas to focus on>
- **Next step**: <Recommended action>

<Repeat for each triggered program.>

<If no programs are triggered:>
> No specific agentic program recommendations based on current findings. As the
> portfolio's agentic readiness improves, re-assess to identify program eligibility.
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

### Analysis Inventory

```markdown
## Analysis Inventory

| # | Service | Report File | Analysis Date | Repo Type | Agent Scope |
|---|---------|-------------|-----------------|-----------|-------------|
| 1 | <service name> | <file path> | <date> | <repo_type> | <agent_scope> |
| <repeat for each service> |
```

---

### Table of Contents

The complete report structure, for reference:

```markdown
# Portfolio Agentic Readiness Analysis Report

1. Executive Dashboard
   - Readiness Distribution
   - Portfolio Summary
   - Repo Type Distribution
   - Blocker Heatmap by Section
   - Readiness Snapshot
2. Cross-Cutting BLOCKERs — Same Blocker in 2+ Repos
3. Cross-Cutting RISKs
   - Cross-Cutting RISK-SAFETY — Recurring Safety Risks Across Portfolio
   - Cross-Cutting RISK-QUALITY — Recurring Quality Risks Across Portfolio
4. Service Dependency Map
5. Portfolio Remediation Guidance
6. Recommended Actions (Agentic Program Recommendations)
7. Portfolio-Level Findings
8. Service-by-Service Summary
9. Analysis Inventory
```
