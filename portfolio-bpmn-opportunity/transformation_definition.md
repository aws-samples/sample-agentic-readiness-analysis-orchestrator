## Name

Portfolio BPMN Agentic Opportunity (BAO) Assessment

## Objective

Aggregate individual repository BAO reports into a portfolio-level analysis that identifies cross-repo agent opportunity patterns, total Bedrock consumption forecast, dependency coverage across the portfolio, and a consolidated implementation roadmap.

## Summary

This transformation consumes multiple individual BAO reports (`*-bpmn-opportunity-report.md` files) from different repositories and produces a comprehensive portfolio-level view focused exclusively on BPMN agentic opportunities. It does NOT cross-reference with ARA or MOD findings. That is the Bridge TD's responsibility.

The transformation follows a 5-step pipeline:
1. **Read Context**: Parse additionalPlanContext for portfolio framing
2. **Discovery**: Locate all BAO report files in the directory structure
3. **Parsing**: Extract opportunity classifications, dependency lists, and cost estimates from each report
4. **Aggregation**: Combine findings across all repos into portfolio-level metrics
5. **Report Generation**: Produce the portfolio BAO report

The output is a Markdown report saved as `{portfolio_name}-portfolio-bao-report.md` at the portfolio root in the `bpmn-opportunity-assessment/` directory.

## Entry Criteria

- At least 1 individual BAO report exists in repository directories
- BAO reports follow the expected structure: opportunity classification table, dependency listing, cost summary
- Write permissions exist to create the output report file

## Implementation Steps

### Step 0: Read additionalPlanContext

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `context` | string | No | -- | Free-text description of the portfolio. Used to frame portfolio-level findings. |
| `service_inventory` | object[] | No | -- | List of services with metadata (name, path, priority, tags). Used to enrich the service-by-service summary. |

### Step 1: Discovery

Scan the directory structure to find all individual BAO reports. Look for files matching `*-bpmn-opportunity-report.md` in `bpmn-opportunity-assessment/` directories within each repository path.

If fewer than 1 report is found, terminate with an error: "No BAO reports found. Run the BPMN Agentic Opportunity assessment on individual repositories first."

### Step 2: Parse Reports

For each BAO report, extract:

- **Process metadata**: process name, repository, BPMN file path
- **Task inventory**: total tasks, agent count, service count, human count
- **Opportunity classification**: per-task category (automate, data-platform, agent-build-now, agent-data-first, human-required)
- **Dependencies**: inferred, declared, unknown counts and details
- **Cost summary**: agent task count, total tokens, estimated monthly cost, recommended models
- **Implementation waves**: which tasks are in wave 1 (build now), wave 2 (data first), wave 3 (system remediation)

### Step 3: Aggregate

Combine findings across all reports:

#### 3.1 Portfolio Opportunity Summary

| Metric | Aggregation |
|--------|-------------|
| Total processes analyzed | Count of reports |
| Total tasks | Sum across all reports |
| Agent opportunities | Sum of agent-classified tasks |
| Automatable tasks | Sum of service-classified tasks |
| Human-required tasks | Sum of human-classified tasks |
| Agent Build-Now | Sum across reports |
| Agent Data-First | Sum across reports |
| Automate | Sum across reports |
| Data Platform | Sum across reports |
| Total estimated monthly Bedrock cost | Sum across reports |

#### 3.2 Cross-Repo Patterns

Identify patterns that appear across multiple repos:

- **Common dependency types**: Which dependency types (service_endpoint, data_store, etc.) appear most frequently?
- **Vendor distribution**: How many dependencies were found by each vendor extractor?
- **Human task patterns**: Are there common human task patterns across repos (approval gates, review tasks)?
- **Cost concentration**: Which repos/processes account for the majority of estimated Bedrock cost?

#### 3.3 Dependency Coverage

Aggregate dependency data across all reports:

- Total inferred dependencies across portfolio
- Total declared dependencies
- Total unknown dependencies (tasks with no system references)
- Breakdown by dependency type and vendor

#### 3.4 Implementation Wave Aggregation

Combine implementation waves across repos:

- **Wave 1 (Build Now)**: All tasks from all repos that are ready to implement
- **Wave 2 (Data First)**: All tasks needing data work before agent deployment
- **Wave 3 (System Remediation)**: All tasks blocked by system issues (populated by Bridge TD after ARA cross-reference)

### Step 4: Generate Report

Save as `bpmn-opportunity-assessment/{portfolio_name}-portfolio-bao-report.md`.

#### Report Structure

```markdown
# Portfolio BAO Report: {portfolio_name}

**Date**: {assessment date}
**Repositories Assessed**: {count}
**Total Processes**: {count}

---

## Portfolio Opportunity Summary

| Metric | Value |
|--------|-------|
| Total Processes Analyzed | {count} |
| Total Tasks | {count} |
| Agent Opportunities | {count} |
| Automatable Tasks | {count} |
| Human-Required Tasks | {count} |
| Estimated Monthly Bedrock Cost | ${amount} |

### Opportunity Breakdown

| Category | Count | % of Total |
|----------|------:|----------:|
| Agent Build-Now | {N} | {%} |
| Agent Data-First | {N} | {%} |
| Automate | {N} | {%} |
| Data Platform | {N} | {%} |
| Human Required | {N} | {%} |

## Process-by-Process Summary

| Repository | Process | Tasks | Agents | Services | Human | Est. Cost/mo |
|-----------|---------|------:|-------:|---------:|------:|-------------:|
| {repo} | {process} | {N} | {N} | {N} | {N} | ${amount} |

## Top Agent Opportunities (ranked by composite score)

| Rank | Task | Process | Repository | Category | Autonomy | Cost/1K |
|-----:|------|---------|-----------|----------|----------|--------:|
| 1 | {task} | {process} | {repo} | {category} | {autonomy} | ${cost} |

## Dependency Coverage

### By Type

| Dependency Type | Count | Confidence |
|----------------|------:|-----------|
| Service Endpoint | {N} | High |
| Data Store | {N} | High |
| Message Flow | {N} | Medium |
| Call Activity | {N} | High |
| Vendor Specific | {N} | Medium |

### By Vendor Extractor

| Vendor | Dependencies Found |
|--------|------------------:|
| bpmn-2.0 | {N} |
| camunda-c7 | {N} |
| camunda-c8 | {N} |
| jbpm | {N} |

### Unknown Dependencies

| Task | Repository | Reason |
|------|-----------|--------|
| {task} | {repo} | {reason} |

> These tasks have no system references in the BPMN model. Run ARA on the target
> systems and use the Bridge TD to cross-reference readiness status.

## Implementation Roadmap

### Wave 1: Build Now ({N} tasks, ${cost}/mo)

Tasks with ready data and deterministic or agent-ready classification:

| Task | Process | Repository | Category | Cost/mo |
|------|---------|-----------|----------|--------:|
| {task} | {process} | {repo} | {category} | ${cost} |

### Wave 2: After Data Work ({N} tasks, ${cost}/mo)

Tasks classified as "Agent Data-First" or "Data Platform":

| Task | Process | Repository | Data Gap |
|------|---------|-----------|----------|
| {task} | {process} | {repo} | {gap description} |

### Wave 3: After System Remediation

> This wave is populated by the Bridge TD after cross-referencing with ARA findings.
> Run a full assessment (assessment_type: full) to identify which agent opportunities
> are blocked by ARA findings on target systems.

## Warnings

| Code | Message | Vendor |
|------|---------|--------|
| {code} | {message} | {vendor} |

## Cost Forecast

| Metric | Value |
|--------|-------|
| Total agent tasks | {count} |
| Total tokens/invocation (all agents) | {sum} |
| Estimated monthly cost | ${amount} |
| At daily volume | {volume} invocations/day |
| Model mix | {models} |

### Cost by Repository

| Repository | Agent Tasks | Est. Monthly Cost |
|-----------|------------:|------------------:|
| {repo} | {N} | ${amount} |
```

## Exit Criteria

- Report file exists at `bpmn-opportunity-assessment/{portfolio_name}-portfolio-bao-report.md`
- All discovered BAO reports are included in the aggregation
- Portfolio summary metrics are consistent (totals match sum of per-repo values)
- Report is valid Markdown with no broken tables

## Constraints

- **Read-only assessment**: Do not modify any source code or individual BAO reports
- **Stay on the current branch**: This is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out and perform all work there.
- **No ARA/MOD cross-referencing**: This TD aggregates BAO data only. Cross-referencing with ARA and MOD findings is the Bridge TD's responsibility.
- **Minimum 1 report**: At least 1 BAO report must exist. Terminate with error if none found.
