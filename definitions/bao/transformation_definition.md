## Name

BPMN Agentic Opportunity Assessment

## Objective

Analyze BPMN 2.0 process models in a repository to identify which process steps are candidates for agentic AI, classify each opportunity by reasoning complexity and data readiness, assign an autonomy level, estimate implementation costs, and produce a prioritized opportunity map with dependency discovery.

This assessment answers the question: given this business process, where should we deploy AI agents, what are the system dependencies, and what does the implementation roadmap look like?

## Summary

This transformation scans a repository for BPMN 2.0 files (`.bpmn`, `.bpmn2`, `.bpmn20.xml`), reads each process model, and evaluates every task element against a classification model that determines whether the task is best handled by an AI agent, a deterministic service, or a human. Each task is scored on four dimensions (AI benefit, complexity, risk, integration effort) and classified into one of four opportunity categories based on reasoning complexity and data readiness.

The assessment produces a structured Markdown report containing:
- Process overview with task inventory
- Per-task classification (agent / service / human-required)
- Opportunity categorization (automate / data platform / agent build-now / agent data-first)
- Autonomy level per agent task (Autonomous / Prepared / Exploration / Guardrail)
- Cost estimation per agent task (tokens, model recommendation, monthly projection)
- Prioritized implementation roadmap
- Dependency listing (inferred from BPMN elements and vendor extensions)

The output is saved as `{process-name}-bpmn-opportunity-report.md`.

## Entry Criteria

- The repository contains at least one BPMN 2.0 file (`.bpmn`, `.bpmn2`, or `.bpmn20.xml`)
- The BPMN analyzer has been run as a pre-processing step, producing a JSON analysis report (see `tools/bpmn-analyzer/run_analysis.py`)
- The JSON analysis report is available at the path specified in `additionalPlanContext` (field: `analysis_report_path`)
- Write permissions exist to create the output report file
- This assessment operates in read-only mode and will not modify any files in the repository
- Stay on the current branch — this is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out and perform all work there.

## Implementation Steps

### Step 0: Read additionalPlanContext

Extract the following fields from `additionalPlanContext`:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `analysis_report_path` | string | **Yes** | -- | Path to the JSON analysis report produced by `tools/bpmn-analyzer/run_analysis.py`. Contains task inventory, constraint profile, task scores, and classification. |
| `context` | string | No | -- | Free-text description of the business process. Used to frame findings. |
| `daily_volume` | integer | No | 100 | Estimated daily invocations per task. Used for cost projection. |
| `priority` | enum | No | -- | P0, P1, P2. Recorded in report metadata. |
| `tags` | string[] | No | -- | User-defined tags for categorization. |
| `ara_report_path` | string | No | -- | **Deprecated.** ARA cross-referencing is handled by the Bridge TD, not the BAO TD. This field is accepted but ignored. If present, the report notes: "ARA cross-referencing is performed by the Bridge TD when running a full assessment." |

### Step 1: Read the Analysis Report

Read the JSON file at `analysis_report_path`. The file is produced by `tools/bpmn-analyzer/run_analysis.py` and contains deterministic, pre-computed analysis:

- `process`: name, ID, element count, flow count
- `constraints`: total count, density, gateway depth, counts by type (ordering, exclusion, coexistence)
- `tasks[]`: per-task scores (ai_benefit, complexity, risk, effort, composite), migration_type (agent/service/human_required), verdict, reasoning, cost_estimate
- `summary`: total tasks, agent/service/human counts, recommended order, monthly cost estimate

**Validation:** Verify the JSON contains the required top-level keys (`process`, `constraints`, `tasks`, `summary`). If any are missing, terminate with an error.

The task scores and migration_type classifications in this JSON are deterministic (computed from BPMN topology and scoring rules, not LLM inference). Do not override them. The subsequent steps add the opportunity classification layer on top.

### Step 2: Apply Opportunity Classification

Using the pre-computed task data from the analysis report, classify each task into one of four opportunity categories. The migration_type (agent/service/human_required) and scores (ai_benefit, complexity, risk, effort) come from the analysis report. This step adds the opportunity category and autonomy level.

#### 2.1 Opportunity Category

Combine the migration type with data readiness. Data readiness is assessed from:

1. **BPMN data associations**: Does the task reference `dataStoreReference` elements (structured, likely ready) or `dataObject` elements with document/file names (unstructured, likely not ready)?
2. **Service task implementations**: Does the task have a WSDL or REST endpoint reference (ready) or no implementation details (unknown)?
3. **Message flows**: Does the task communicate with external participants (check if API-based or manual)?
4. **Task name inference**: "Check credit score" implies API call (ready). "Review documents from multiple sources" implies scattered data (not ready).
5. **ARA DATA findings**: If an ARA report exists (via `ara_report_path`), use the DATA section findings for the target system. DATA BLOCKER = not ready. DATA RISK = partial. No DATA findings = ready.

| Migration Type | Data Readiness | Category |
|---|---|---|
| service | Ready | **Automate** |
| service | Not ready | **Data Platform** |
| agent | Ready | **Agent (build now)** |
| agent | Not ready / Unknown | **Agent (data first)** |
| human-required | Any | **Human Required** |

When data readiness cannot be determined (no BPMN metadata, no ARA report), classify as "Unknown" and note in the report: "Data readiness could not be assessed from the BPMN model. Run ARA on the target systems for a complete classification."

#### 2.2 Autonomy Level

Assign to each task classified as "agent":

| Risk Score | Autonomy Level | Description |
|---|---|---|
| < 0.2 | **Autonomous** | Agent decides and acts. Human notified after. |
| 0.2 -- 0.4 | **Prepared** | Agent synthesizes and recommends. Human reviews and approves. |
| 0.4 -- 0.6 | **Exploration** | Human leads investigation. Agent surfaces data in real time. |
| > 0.6 | **Guardrail** | Human acts freely. Agent monitors for errors. |

If the task has regulatory or compliance signals (keywords: regulatory, compliance, legal, audit), cap autonomy at Prepared regardless of risk score.

### Step 3: List Dependencies

Extract the `dependencies` section from the analysis JSON report. List all inferred, declared, and unknown dependencies in the report. Do NOT cross-reference with ARA findings -- that is the Bridge TD's responsibility.

For each dependency, record:
- Source task ID and name
- Target type (service_endpoint, data_store, message_flow, call_activity, vendor_specific)
- Target reference (endpoint URL, class name, data store name, etc.)
- Confidence (high/medium/low)
- Vendor that detected it (bpmn-2.0, camunda-c7, camunda-c8, jbpm, etc.)

For unknown dependencies (user tasks with no system references), note them as requiring further investigation.

Include any warnings from the dependency extraction (unsupported vendor namespaces, etc.).

### Step 4: Generate Report

Save the report as `{process-name}-bpmn-opportunity-report.md` in the `bpmn-opportunity-assessment/` directory.

#### Report Structure

```markdown
# BPMN Agentic Opportunity Assessment: {Process Name}

**Repository**: {repo path}
**BPMN File**: {file path}
**Date**: {assessment date}
**Context**: {from additionalPlanContext, if provided}
**Daily Volume**: {daily_volume}

---

## Summary

{Process name} contains {N} tasks. {X} are agent opportunities ({X1} build-now, {X2} data-first), {Y} are automatable with deterministic logic, and {Z} require human involvement. Estimated monthly Bedrock cost for agent tasks: ${amount} at {daily_volume} invocations/day.

## Opportunity Classification

| Task | Type | BPMN Element | AI Benefit | Risk | Category | Autonomy | Cost/1K |
|------|------|-------------|------------|------|----------|----------|---------|
| {name} | agent | userTask | 0.75 | 0.35 | Build now | Prepared | $2.40 |
| {name} | service | serviceTask | 0.20 | 0.10 | Automate | -- | -- |
| {name} | human | userTask | 0.80 | 0.70 | Human Required | -- | -- |

## Agent Opportunities (ranked by composite score)

### 1. {Task Name}
- **Category**: Agent (build now)
- **Autonomy**: Prepared -- Agent synthesizes and recommends. Human reviews and approves.
- **Scores**: AI Benefit: {score} | Complexity: {score} | Risk: {score} | Effort: {score} | Composite: {score}
- **Data Readiness**: {Ready / Not Ready / Unknown} -- {reasoning}
- **Cost**: ~${cost}/1K invocations ({model}, {tokens} tokens)
- **Structural Position**: {ordering, branching, parallelism facts}
- **Integration Approach**: {how BPM engine connects to agent}
- **Prerequisites**: {what needs to be in place}

### 2. {Next Task}
...

## Automatable Tasks

| Task | BPMN Element | Recommendation |
|------|-------------|----------------|
| {name} | serviceTask | Step Functions / rule engine |

## Human-Required Tasks

| Task | BPMN Element | Risk Score | Reason |
|------|-------------|------------|--------|
| {name} | userTask | 0.70 | Approval gate, regulatory requirement |

## Data Readiness Gaps

| Task | Data Source | Current State | Remediation |
|------|-----------|---------------|-------------|
| {name} | {source} | {scattered/unstructured/no API} | {what to build} |

## Dependencies

| Source Task | Target | Type | Confidence | Vendor |
|---|---|---|---|---|
| {task} | {target_ref} | {type} | {confidence} | {vendor} |

### Unknown Dependencies

| Task | Reason |
|------|--------|
| {task} | {reason} |

*ARA cross-referencing is performed by the Bridge TD when running a full assessment (assessment_type: full). Run the full assessment to see which agent opportunities are blocked by ARA findings.*

## Implementation Roadmap

### Wave 1: Build Now
{Agent tasks where data is ready and systems are ready (or no ARA blockers)}

### Wave 2: After Data Work
{Agent tasks in the "data first" category}

### Wave 3: After System Remediation
{Agent tasks where ARA identified blockers on target systems}

## Process Structure Summary

- **Total elements**: {count}
- **Tasks**: {count} | **Gateways**: {count} | **Events**: {count}
- **Exclusive branches (XOR)**: {count}
- **Parallel branches (AND)**: {count}
- **Linear chains**: {count}
- **Key structural insight**: {1-2 sentences about the process topology}

## Cost Summary

| Metric | Value |
|--------|-------|
| Agent tasks | {count} |
| Total tokens/invocation (all agents) | {sum} |
| Estimated monthly cost ({daily_volume}/day) | ${amount} |
| Recommended models | {list} |
```

## Exit Criteria

- Four-artifact bundle exists at `bpmn-opportunity-assessment/`:
  - `{process-name}-bpmn-opportunity-report.md`
  - `{process-name}-bpmn-opportunity-report.json`
  - `{process-name}-bpmn-opportunity-report.html`
  - `{process-name}-bpmn-opportunity-report.metadata.json`
- All tasks in the BPMN process are classified (no task left unclassified)
- Each agent task has a cost estimate
- JSON artifact passes schema validation (all required fields present)
- Report is valid Markdown with no broken tables

## Constraints and Guardrails

Strictly follow these rules at all times:

- **Read-only assessment**: Do not modify any source code, BPMN files, configuration, or infrastructure in the repository. Only create the output artifact bundle (md + json + html + metadata.json).
- **Stay on the current branch**: This is an analysis-only task. Do not create, switch, or checkout any git branches. Remain on whatever branch is currently checked out and perform all work there.
- **Deterministic extraction is ground truth**: The JSON analysis report produced by `tools/bpmn-analyzer/run_analysis.py` contains pre-computed scores and classifications. Do not override the migration_type or composite scores. The opportunity classification layer (Step 2) adds category and autonomy on top of the analyzer's output.
- **Be specific, cite BPMN elements**: Always reference actual task IDs, element types, and BPMN file paths. Never write "there may be..." -- state what was found in the process model.
- **ARA cross-referencing is the Bridge TD's responsibility**: Do not attempt to cross-reference BAO findings with ARA or MOD findings. Note in the report: "ARA cross-referencing is performed by the Bridge TD when running a full assessment."
- **No LLM involvement in extraction**: The BPMN analyzer's constraint extraction, dependency discovery, and task scoring are deterministic Python. The TD adds the opportunity classification layer (category + autonomy) which uses LLM reasoning. Keep these layers distinct.
- **Report completeness**: The output report must contain all required sections: metadata header, summary, opportunity classification table, agent opportunities (ranked), automatable tasks, human-required tasks, data readiness gaps, dependencies, implementation roadmap, process structure summary, and cost summary.

## Four-Artifact Output Contract

Every per-repo BAO assessment emits four artifacts: three report artifacts plus a metadata sidecar.

### Artifacts

| Artifact | Filename | Purpose |
|---|---|---|
| Markdown report | `{process}-bpmn-opportunity-report.md` | Richest-prose artifact. Carries opportunity narratives, dependency analysis, implementation roadmap, and cost projections. |
| JSON report | `{process}-bpmn-opportunity-report.json` | **Canonical machine-readable contract.** Consumed by webapp and Portfolio BAO TD. Every task classification, dependency, and cost field is present. |
| HTML report | `{process}-bpmn-opportunity-report.html` | Single self-contained HTML file. Renders opportunity breakdown, dependency graph, implementation waves, and cost forecast. |
| Metadata sidecar | `{process}-bpmn-opportunity-report.metadata.json` | Tiny JSON file carrying version compatibility data. |

The JSON artifact is the canonical contract. If any artifacts disagree on a field, JSON wins.

### Metadata Sidecar

```json
{
  "assessment_type": "bao",
  "assessment_date": "2026-05-12",
  "td_version": "bpmn-opportunity-assessment",
  "bpmn_analyzer_version": "1.0.0",
  "process_name": "{process_name}",
  "bpmn_file": "{bpmn_file_path}"
}
```

### JSON Schema

The canonical JSON report follows this structure:

```json
{
  "metadata": {
    "assessment_type": "bao",
    "assessment_date": "2026-05-12",
    "td_version": "bpmn-opportunity-assessment",
    "process_name": "Invoice Receipt",
    "bpmn_file": "src/main/resources/invoice.v2.bpmn",
    "repository": "./services/invoice-process",
    "daily_volume": 200,
    "context": "Camunda 7 invoice receipt process"
  },
  "summary": {
    "total_tasks": 12,
    "agent_tasks": 3,
    "service_tasks": 7,
    "human_required_tasks": 2,
    "categories": {
      "agent_build_now": 1,
      "agent_data_first": 2,
      "automate": 5,
      "data_platform": 2,
      "human_required": 2
    },
    "estimated_monthly_cost_usd": 558.90,
    "daily_volume": 200
  },
  "tasks": [
    {
      "task_id": "serviceTask_12",
      "task_name": "Review Credit Score",
      "bpmn_element_type": "userTask",
      "migration_type": "agent",
      "category": "agent_build_now",
      "autonomy_level": "prepared",
      "scores": {
        "ai_benefit": 0.75,
        "complexity": 0.45,
        "risk": 0.35,
        "effort": 0.30,
        "composite": 0.72
      },
      "cost_estimate": {
        "tokens_per_invocation": 2400,
        "model": "claude-3-haiku",
        "cost_per_1k_invocations_usd": 2.40,
        "monthly_cost_usd": 14.40
      },
      "data_readiness": "ready",
      "data_readiness_reasoning": "Task references dataStoreReference with structured API access",
      "structural_position": "After XOR gateway, parallel branch with timer boundary",
      "dependencies": [
        {
          "target_type": "service_endpoint",
          "target_ref": "com.example.CreditScoreDelegate",
          "confidence": "high",
          "vendor": "camunda-c7"
        }
      ]
    }
  ],
  "dependencies": {
    "inferred": [
      {
        "source_task_id": "serviceTask_12",
        "source_task_name": "Review Credit Score",
        "target_type": "service_endpoint",
        "target_ref": "com.example.CreditScoreDelegate",
        "confidence": "high",
        "vendor": "camunda-c7"
      }
    ],
    "declared": [],
    "unknown": [
      {
        "source_task_id": "userTask_5",
        "source_task_name": "Manual Underwriter Review",
        "reason": "User task with no system references"
      }
    ]
  },
  "implementation_waves": {
    "wave_1_build_now": ["serviceTask_12"],
    "wave_2_data_first": ["userTask_3", "userTask_7"],
    "wave_3_system_remediation": []
  },
  "process_structure": {
    "total_elements": 45,
    "tasks": 12,
    "gateways": 5,
    "events": 8,
    "xor_branches": 3,
    "parallel_branches": 1,
    "linear_chains": 4
  },
  "warnings": []
}
```

### Per-Task Required Fields

Every task in the `tasks` array MUST carry these fields:

| Field | Type | Description |
|---|---|---|
| `task_id` | string | BPMN element ID |
| `task_name` | string | Human-readable task name from BPMN |
| `bpmn_element_type` | string | BPMN element type (serviceTask, userTask, businessRuleTask, etc.) |
| `migration_type` | enum | `agent`, `service`, `human_required` (from analyzer) |
| `category` | enum | `agent_build_now`, `agent_data_first`, `automate`, `data_platform`, `human_required` |
| `autonomy_level` | enum or null | `autonomous`, `prepared`, `exploration`, `guardrail`, or null (non-agent tasks) |
| `scores` | object | `ai_benefit`, `complexity`, `risk`, `effort`, `composite` (all 0.0-1.0) |
| `cost_estimate` | object or null | `tokens_per_invocation`, `model`, `cost_per_1k_invocations_usd`, `monthly_cost_usd` (null for non-agent) |
| `data_readiness` | enum | `ready`, `not_ready`, `unknown` |
| `data_readiness_reasoning` | string | Why this classification was assigned |
| `structural_position` | string | Position in the process flow (ordering, branching context) |
| `dependencies` | array | Dependencies inferred for this specific task |

### HTML Visual Contract

The per-repo BAO HTML artifact is a single self-contained HTML file (no external asset fetches). Tab order: **summary → opportunities → dependencies → roadmap → costs**.

**Header:**
- Title: `{process_name} - BPMN Agentic Opportunity Report`
- Subtitle: `{date} · {total_tasks} tasks · {agent_tasks} agent opportunities · ${monthly_cost}/mo`

**Summary Tab:**
- Donut chart: task classification breakdown (agent build-now, agent data-first, automate, data platform, human required)
- Stats cards: total tasks, agent opportunities, estimated monthly cost, daily volume

**Opportunities Tab:**
- Table: ranked agent opportunities with task name, category, autonomy level, composite score, cost/1K
- Expandable rows with scores breakdown, data readiness, structural position

**Dependencies Tab:**
- Table: all dependencies with source task, target, type, confidence, vendor
- Summary cards: by type count, by vendor count, unknown count

**Roadmap Tab:**
- Three-wave visualization: Wave 1 (build now), Wave 2 (data first), Wave 3 (system remediation)
- Each wave shows tasks with their category and estimated cost

**Costs Tab:**
- Bar chart: cost by task
- Summary: total monthly cost, model mix, tokens per invocation

