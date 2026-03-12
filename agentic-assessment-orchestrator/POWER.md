---
name: "agentic-assessment-orchestrator"
displayName: "Agentic Assessment Orchestrator"
description: "Orchestrate comprehensive agentic readiness assessments across multiple repositories with portfolio-level analysis, dependency mapping, and coordinated modernization roadmaps."
keywords: ["agentic", "assessment", "portfolio", "modernization", "aws", "readiness", "transformation", "dependencies"]
author: "AWS"
---

# Agentic Assessment Orchestrator

## Overview

This Knowledge Base Power turns Kiro into an orchestrator for running comprehensive agentic readiness assessments across your entire service portfolio. Kiro reads your `portfolio-config.yaml`, handles repository cloning when needed, and coordinates two AWS Transform Custom transformations in sequence:

1. **Individual Repository Assessment** — Kiro spawns parallel subagents, one per repository, each running `atx custom def exec` concurrently to evaluate the codebase against 56 agentic readiness criteria across 5 categories
2. **Portfolio Assessment** — After all individual assessments complete, Kiro runs the portfolio transformation to aggregate results, identify cross-cutting concerns, map service dependencies, and produce a portfolio-wide modernization roadmap

The transformation definition names are configurable in `portfolio-config.yaml` via the `transformation_definitions` section — use whatever names you published to your AWS Transform registry.

**How Kiro Orchestrates:**
- Parses `portfolio-config.yaml` to discover all repositories, their configuration, the `goal`, `goal_context`, `preferences`, and the transformation definition names
- Validates the `goal` value — must be one of `agentic-ai-enablement`, `cloud-native-modernization`, `cost-optimization`, `general-readiness`; defaults to `general-readiness` if missing or unrecognized (with a warning for unrecognized values)
- Validates per-repo fields: `name` and `path` required; `priority`, `context`, `preferences`, `repo_type`, `tags` optional
- Clones repositories automatically when `repository_url` is provided and the local `path` doesn't exist
- For each repository, Kiro generates a temporary ATX configuration file containing the service's `additionalPlanContext` — including `goal`, `goal_context`, `repo_type` (if specified), `context`, merged `preferences` (global + per-repo with conflict resolution), `priority`, and `tags`
- Spawns parallel subagents — one per repository — to run `atx custom def exec -n <individual_assessment> -g file://<generated-config> -x -t` concurrently
- Waits for all individual assessments to complete
- Generates a portfolio-level ATX configuration file with `additionalPlanContext` containing `goal`, `goal_context`, global `preferences`, the full service inventory, and dependency overrides
- Runs `atx custom def exec -n <portfolio_assessment> -g file://<generated-portfolio-config> -x -t` to generate the aggregated report
- Consolidates all reports into a single `agentic-readiness-assessment/` folder at the portfolio root — copies individual reports from each repo, alongside the portfolio report — and cleans up temporary `.atx-config-*.yaml` files

> All `atx` commands MUST use `-x` (non-interactive) and `-t` (trust all tools) flags since assessments run at scale without human intervention.

> **⏱ Long-Running Commands — Timeout Handling:** `atx custom def exec` commands are long-running operations that typically take **5–15 minutes per repository** depending on codebase size. These commands **will likely exceed default shell timeouts**. Subagents MUST NOT hang waiting for output or assume the command failed just because it took a long time. Instead, subagents should:
> 1. Launch the `atx` command with an appropriate timeout (or no timeout)
> 2. **Do NOT poll, retry, or re-check repeatedly.** After launching the command, wait patiently. Do not check status in a loop or re-run the command. A single check after a reasonable wait (10–15 minutes) is sufficient.
> 3. If the command times out or appears to hang, check **once** whether the assessment report file was generated at the expected output path
> 4. Validate success by checking for the existence of the output report file: `{repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md`
> 5. If the report exists, treat the assessment as successful regardless of the command's exit behavior
> 6. Only report failure if the report file is missing AND the command returned a clear error
> 7. **Never retry a transformation that is still running.** Running duplicate `atx` processes against the same repo wastes resources and can cause conflicts.

**What You Get:**
- Goal-driven assessment framing aligned to your modernization objective
- Dependency-aware modernization roadmaps that respect service relationships
- Cross-cutting concern identification (gaps affecting 3+ services), split by goal priority
- Integration opportunities (shared services, event-driven architecture)
- Resource allocation recommendations (team structure, skill gaps, training)
- Risk analysis with mitigation strategies
- Configurable preferences to match your technology constraints

**When to Use:**
- Planning agentic AI adoption across microservices
- Identifying shared infrastructure gaps
- Prioritizing modernization based on dependencies
- Tracking portfolio-wide readiness progress
- Generating executive-level portfolio reports

---

## Prerequisites

Kiro orchestrates the assessment workflow, but relies on **AWS Transform CLI** to execute the actual transformations. You need:

1. **AWS Transform CLI** installed and configured
   ```bash
   # Check if installed
   atx --version
   
   # If not installed, follow: https://docs.aws.amazon.com/transform/
   ```

2. **Transformation definitions** published to your AWS Transform registry. The names are configured in `portfolio-config.yaml`:
   ```yaml
   transformation_definitions:
     individual_assessment: "your-individual-assessment-name"
     portfolio_assessment: "your-portfolio-assessment-name"
   ```
   Verify they exist:
   ```bash
   atx custom def list | grep your-assessment-name
   ```

3. **Repository access** — Repositories can be:
   - Already cloned locally (just set `path` in the config)
   - Auto-cloned by Kiro (set `repository_url` and `path` in the config — Kiro clones if `path` doesn't exist)

---

## Quick Start

### 1. Create Portfolio Configuration

Create `portfolio-config.yaml` defining which services to assess, the modernization goal, and any technology preferences:

```yaml
portfolio_name: "my-platform"
goal: "agentic-ai-enablement"
goal_context: "Building customer-facing AI agents for support and order management"

transformation_definitions:
  individual_assessment: "individual-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka"]

repositories:
  - name: "service-a"
    repository_url: "https://github.com/org/service-a.git"  # optional - Kiro clones if path doesn't exist
    path: "./services/service-a"
    priority: "P0"
    context: "Main order processing service, handles 80% of traffic"
    preferences:
      prefer: ["dynamodb"]
      avoid: ["rds"]
  - name: "service-b"
    path: "./services/service-b"  # already cloned locally
    priority: "P1"
    tags: ["backend", "inventory"]
```

See `portfolio-config.example.yaml` for complete examples with preferences.

### 2. Ask Kiro to Run the Portfolio Assessment

```
"Run the agentic assessment orchestrator on portfolio-config.yaml"
```

Kiro will:
1. Parse `portfolio-config.yaml` — read `goal`, `goal_context`, `preferences`, `transformation_definitions`, `repositories`, and `dependency_overrides`
2. Validate the `goal` value:
   - Must be one of: `agentic-ai-enablement`, `cloud-native-modernization`, `cost-optimization`, `general-readiness`
   - If unrecognized → warn the user and default to `general-readiness`
   - If missing → default to `general-readiness`
3. Validate per-repo fields: `name` and `path` are required; `priority`, `context`, `preferences`, `repo_type`, `tags`, `repository_url`, `report_path` are optional
4. Clone any repositories where `repository_url` is provided and `path` doesn't exist yet
5. For each repository, generate a temporary ATX config file (e.g., `.atx-config-<service-name>.yaml`) with `additionalPlanContext` containing: `goal`, `goal_context`, `repo_type` (if specified), `context`, merged `preferences`, `priority`, and `tags`
6. Spawn parallel subagents — one per repository — each running `atx custom def exec -n <individual_assessment> -p <repo-path> -g file://.atx-config-<service-name>.yaml -x -t`
7. Wait for all subagents to complete
8. Generate a portfolio-level ATX config file (e.g., `.atx-config-portfolio.yaml`) with `additionalPlanContext` containing: `goal`, `goal_context`, global `preferences`, the full service inventory, and dependency overrides
9. Run `atx custom def exec -n <portfolio_assessment> -p . -g file://.atx-config-portfolio.yaml -x -t` to generate the aggregated portfolio report
10. Consolidate all reports — copy individual assessment reports from each repo's `agentic-readiness-assessment/` directory into a single `agentic-readiness-assessment/` folder at the portfolio root, alongside the portfolio report. Clean up temporary `.atx-config-*.yaml` files.

### 3. Or Run Manually Step by Step

**Individual assessments (repeat for each repo):**
```bash
cd ./services/my-service
atx custom def exec -n <your-individual-assessment-name> -p . -g file://atx-config.yaml -x -t
```

Where `atx-config.yaml` contains the new simplified `additionalPlanContext`:
```yaml
additionalPlanContext: |
  goal: "agentic-ai-enablement"
  goal_context: "Building a customer support agent for order and inventory data"
  repo_type: "application"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  preferences:
    prefer: ["eks", "aurora", "bedrock", "dynamodb"]
    avoid: ["self-managed-kafka", "rds"]
  priority: "P0"
  tags: ["monolith", "php"]
```

**Portfolio assessment (after all individual assessments):**
```bash
atx custom def exec -n <your-portfolio-assessment-name> -p . -g file://atx-portfolio-config.yaml -x -t
```

Where `atx-portfolio-config.yaml` contains:
```yaml
additionalPlanContext: |
  goal: "agentic-ai-enablement"
  goal_context: "Building customer-facing AI agents for support and order management"
  preferences:
    prefer: ["eks", "aurora", "bedrock"]
    avoid: ["self-managed-kafka"]
  
  Portfolio: my-platform
  Services assessed: 2
  
  Service inventory:
  - service-a (P0, ./services/service-a) — Tags: monolith, php
  - service-b (P1, ./services/service-b) — Tags: backend, inventory
  
  Dependency overrides:
  - service-a -> service-b (sync): REST API calls for inventory checks
```

> Always use `-x` (non-interactive) and `-t` (trust all tools) when running at scale. Note: these commands are long-running (5–15 min each). If a command times out, check for the output report file before assuming failure.

---

## Portfolio Configuration

### Basic Configuration

Create a `portfolio-config.yaml` file to define which repositories to assess, the modernization goal, and any technology preferences. Kiro will parse this file to orchestrate the assessment workflow. See `portfolio-config.example.yaml` for a complete example.

**Minimum Configuration:**

```yaml
portfolio_name: "my-platform"
goal: "general-readiness"

transformation_definitions:
  individual_assessment: "individual-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"

repositories:
  - name: "service-a"
    path: "./services/service-a"
  - name: "service-b"
    path: "./services/service-b"
```

**With Goal, Preferences, and Repository Cloning:**

```yaml
portfolio_name: "my-platform"
goal: "agentic-ai-enablement"
goal_context: "Building customer-facing AI agents for support and order management"

transformation_definitions:
  individual_assessment: "individual-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka"]

repositories:
  - name: "service-a"
    repository_url: "https://github.com/org/service-a.git"  # Kiro clones if path doesn't exist
    path: "./services/service-a"
    priority: "P0"
    context: "Main order processing service"
  - name: "service-b"
    path: "./services/service-b"  # Already cloned locally
    priority: "P1"
    tags: ["backend", "inventory"]
```

**Advanced Configuration:**

```yaml
portfolio_name: "ecommerce-platform"
goal: "cloud-native-modernization"
goal_context: "Decomposing monolith into containerized microservices for EKS"

transformation_definitions:
  individual_assessment: "my-team-agentic-assessment"
  portfolio_assessment: "my-team-portfolio-assessment"

preferences:
  prefer: ["eks", "aurora", "fargate"]
  avoid: ["self-managed-kafka", "oracle"]

repositories:
  - name: "checkout-service"
    repository_url: "https://github.com/org/checkout.git"
    path: "./services/checkout"
    priority: "P0"
    context: "Monolithic checkout handling payments and orders"
    preferences:
      avoid: ["serverless"]  # Override: no Lambda for this service
      
  - name: "inventory"
    path: "./services/inventory"
    priority: "P1"
    preferences:
      prefer: ["dynamodb"]
    tags: ["backend", "data"]

  - name: "infra-repo"
    path: "./infrastructure"
    repo_type: "infrastructure-only"
    priority: "P2"

dependency_overrides:
  - source: "checkout-service"
    target: "inventory"
    type: "sync"
    description: "REST API calls for inventory checks"
```

### Goal Configuration

The `goal` field drives how the assessment is framed — which pathways are highlighted, how the roadmap is phased, and which criteria are prioritized. Four predefined goals are supported:

| Goal | Description |
|------|-------------|
| `agentic-ai-enablement` | Enable agentic AI workflows — autonomous agents discovering, invoking, and orchestrating app capabilities |
| `cloud-native-modernization` | Decompose and modernize into cloud-native architectures using managed services, containers, and serverless |
| `cost-optimization` | Reduce costs through license elimination, managed service adoption, and right-sizing |
| `general-readiness` | Comprehensive assessment across all dimensions with no specific weighting (default) |

**Goal Validation:**
- If `goal` is missing → defaults to `general-readiness`
- If `goal` is not one of the 4 predefined values → Kiro warns the user ("Unrecognized goal '{value}', defaulting to general-readiness") and defaults to `general-readiness`
- The `goal_context` free-text field is optional and provides additional context for scoping recommendations (e.g., "Building a customer support agent that needs access to order and inventory data")

### Preferences

The `preferences` object replaces all previous nested constraint objects (`database_constraints`, `deployment_constraints`, `compliance_requirements`, `budget_constraints`, `timeline_constraints`, `modernization_approach`, `custom_constraints`, `avoid_patterns`, `prefer_patterns`, etc.). It uses two flat arrays:

```yaml
preferences:
  prefer: ["eks", "aurora", "bedrock"]    # Technologies/patterns to recommend
  avoid: ["self-managed-kafka", "oracle"]  # Technologies/patterns to avoid
```

The agent interprets preferences intelligently:
- `avoid: ["serverless"]` → don't recommend Lambda, prefer containers
- `prefer: ["eks", "aurora"]` → recommend EKS for compute, Aurora for databases
- `avoid: ["microservices-decomposition"]` → keep as monolith, focus on containerization

**Preference Merging:** Per-repo `prefer`/`avoid` arrays are appended to global arrays. If a value appears in both global `prefer` and per-repo `avoid`, the per-repo `avoid` wins (more specific overrides less specific).

### Configuration Schema

The full configuration schema is available in `portfolio-config.schema.json`. Key sections:

- **portfolio_name** (required): Name identifier for the portfolio
- **goal** (required): One of `agentic-ai-enablement`, `cloud-native-modernization`, `cost-optimization`, `general-readiness`
- **goal_context** (optional): Free-text context for scoping recommendations
- **transformation_definitions** (required): Names of the AWS Transform definitions to use
  - `individual_assessment` (required): Name for per-repository assessments
  - `portfolio_assessment` (required): Name for portfolio aggregation
- **preferences** (optional): Global technology/pattern preferences
  - `prefer` (optional): String array of preferred technologies/patterns
  - `avoid` (optional): String array of technologies/patterns to avoid
- **repositories** (required): List of services to assess
  - `name` (required): Service identifier
  - `path` (required): Local path to repository
  - `repository_url` (optional): Git URL — Kiro clones if `path` doesn't exist
  - `priority` (optional): P0 (critical), P1 (high), P2 (medium)
  - `context` (optional): Free-text description of the service
  - `preferences` (optional): Per-repo preference overrides (same `prefer`/`avoid` format)
  - `repo_type` (optional): Override auto-detection — one of `application`, `infrastructure-only`, `deployment-cicd`, `monorepo`, `library`
  - `tags` (optional): String array of tags for categorization
  - `report_path` (optional): Custom output path for the assessment report
- **dependency_overrides** (optional): Manual dependency declarations
  - `source` (required): Source service name
  - `target` (required): Target service name
  - `type` (required): Dependency type (e.g., `sync`, `async`)
  - `description` (optional): Description of the dependency

## Preferences

Control how recommendations are generated using flat `prefer` and `avoid` arrays. These replace all previous nested constraint objects.

### Global Preferences

Set at the portfolio level — apply to all repositories unless overridden:

```yaml
preferences:
  prefer: ["eks", "aurora", "bedrock", "fargate"]
  avoid: ["self-managed-kafka", "oracle", "kubernetes"]
```

### Per-Repo Preference Overrides

Override or extend global preferences for specific repositories:

```yaml
repositories:
  - name: "checkout-service"
    path: "./services/checkout"
    preferences:
      prefer: ["dynamodb"]           # Appended to global prefer
      avoid: ["serverless", "rds"]   # Appended to global avoid
```

### Preference Merging Rules

When generating the per-repo ATX config, Kiro merges global and per-repo preferences:

1. Per-repo `prefer` items are appended to global `prefer`
2. Per-repo `avoid` items are appended to global `avoid`
3. **Conflict resolution:** If a value appears in both global `prefer` and per-repo `avoid`, the per-repo `avoid` wins (more specific overrides less specific). The conflicting value is removed from the merged `prefer` list.

**Example:**
```yaml
# Global
preferences:
  prefer: ["eks", "aurora", "rds"]
  avoid: ["oracle"]

# Per-repo
repositories:
  - name: "service-a"
    preferences:
      prefer: ["dynamodb"]
      avoid: ["rds"]  # Conflicts with global prefer — per-repo avoid wins

# Merged result for service-a:
# prefer: ["eks", "aurora", "dynamodb"]   ← "rds" removed due to per-repo avoid
# avoid: ["oracle", "rds"]               ← per-repo avoid appended
```

### Common Preference Patterns

```yaml
# Keep as monolith, containerize only
preferences:
  prefer: ["ecs", "fargate"]
  avoid: ["microservices-decomposition"]

# Cost-focused: eliminate licenses
preferences:
  prefer: ["aurora-postgresql", "opensearch", "linux"]
  avoid: ["oracle", "sql-server", "windows"]

# Agent-focused: enable AI capabilities
preferences:
  prefer: ["bedrock", "opensearch-serverless", "api-gateway"]
  avoid: ["self-managed-ml-infrastructure"]
```

---

## AWS Transform CLI Reference

### Execute Transformation

```bash
atx custom def exec \
  -n <transformation-name> \
  -p <code-repository-path> \
  -g file://<configuration-file> \
  -x \
  -t
```

**Key Options:**
- `-n, --transformation-name` - Name of the transformation definition
- `-p, --code-repository-path` - Path to repository (use `.` for current directory)
- `-g, --configuration` - Path to config file (with `file://` prefix) or inline `key=value` pairs. Supports `additionalPlanContext` to pass extra context to the transformation agent
- `-t, --trust-all-tools` - Trust all tools (no prompts)
- `-x, --non-interactive` - Run without user assistance (mandatory for parallel/batch execution)
- `--tv, --transformation-version` - Specific version to use

**Configuration File Format:**

The `-g` flag accepts an ATX execution configuration file (YAML or JSON), not arbitrary data. To pass portfolio or service context to the transformation, use the `additionalPlanContext` field:

```yaml
# atx-config.yaml
additionalPlanContext: |
  goal: "cloud-native-modernization"
  goal_context: "Decomposing monolith into containerized microservices"
  context: "Legacy Java monolith running on EC2"
  preferences:
    prefer: ["eks", "fargate"]
    avoid: ["serverless"]
  priority: "P0"
  tags: ["monolith", "java"]
```

```bash
atx custom def exec -n my-assessment -p ./services/checkout -g file://atx-config.yaml -x -t
```

### List Available Transformations

```bash
atx custom def list
atx custom def list --json
```

### Get Transformation Details

```bash
atx custom def get -n <transformation-name>
atx custom def get -n <transformation-name> --tv <version>
```

### Interactive Mode

```bash
atx                           # Start new conversation
atx --resume                  # Resume most recent conversation
atx -t                        # Start with all tools trusted
```

**Full CLI Reference:** https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html

---

## Workflow

### How Kiro Orchestrates the Assessment

When you ask Kiro to run the portfolio assessment, it follows this sequence:

```
portfolio-config.yaml
        │
        ▼
┌─────────────────────┐
│  1. Parse YAML       │  Kiro reads portfolio-config.yaml
│     config file      │  and extracts goal, preferences,
│                      │  repositories, and dependencies
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. Validate goal    │  Must be one of 4 predefined values
│     & config fields  │  Default to general-readiness if
│                      │  missing or unrecognized
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  3. Clone repos      │  For each repo with repository_url
│     (if needed)      │  where path doesn't exist yet
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  4. Generate ATX     │  For each repo, create .atx-config-<name>.yaml
│     config files     │  with goal, merged preferences, context,
│                      │  repo_type, priority, tags
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│  5. Run individual assessments IN PARALLEL   │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Subagent │ │ Subagent │ │ Subagent │ ... │
│  │ repo-a   │ │ repo-b   │ │ repo-c   │     │
│  │atx -g -xt│ │atx -g -xt│ │atx -g -xt│     │
│  └──────────┘ └──────────┘ └──────────┘     │
└─────────────────────┬───────────────────────┘
                      │  (wait for all to complete)
                      ▼
┌─────────────────────┐
│  6. Generate         │  Create .atx-config-portfolio.yaml with
│     portfolio config │  goal, preferences, service inventory,
│                      │  & dependency overrides
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  7. Run portfolio    │  atx custom def exec
│     assessment       │  -n <portfolio_assessment>
│                      │  -p . -g file://.atx-config-portfolio.yaml -x -t
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  8. Consolidate      │  Copy all reports into single
│     reports          │  agentic-readiness-assessment/ folder
│                      │  at portfolio root. Clean up temp files.
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  9. Review reports   │  All reports in one place
└─────────────────────┘
```

### Step 0: Ensure Repositories Are Available

Kiro handles this automatically when `repository_url` is provided in the config. If a repository's `path` doesn't exist locally, Kiro clones it:

```bash
git clone <repository_url> <path>
```

If repositories are already present at their configured `path`, Kiro skips cloning.

For manual setup:
```bash
mkdir -p ./services
git clone https://github.com/org/service-a.git ./services/service-a
```

### Step 1: Run Individual Assessments (Parallel)

Kiro spawns one subagent per repository from `portfolio-config.yaml`. For each repository, Kiro first generates a temporary ATX configuration file that passes the service's context via `additionalPlanContext`. This includes the portfolio-level `goal`, merged preferences, and per-repo metadata.

**Generated ATX config example** (`.atx-config-checkout-service.yaml`):
```yaml
additionalPlanContext: |
  goal: "agentic-ai-enablement"
  goal_context: "Building customer-facing AI agents for support and order management"
  context: "Monolithic checkout handling payments and orders"
  preferences:
    prefer: ["eks", "aurora", "bedrock", "dynamodb"]
    avoid: ["self-managed-kafka", "serverless"]
  priority: "P0"
  tags: ["backend", "payment", "critical-path"]
```

If the repo has a `repo_type` specified in the portfolio config, it is included:
```yaml
additionalPlanContext: |
  goal: "agentic-ai-enablement"
  goal_context: "Building customer-facing AI agents for support and order management"
  repo_type: "infrastructure-only"
  preferences:
    prefer: ["eks", "aurora", "bedrock"]
    avoid: ["self-managed-kafka"]
  priority: "P2"
```

Each subagent then runs the individual assessment transformation concurrently:

```bash
# Each subagent runs independently, using the name from transformation_definitions.individual_assessment:
atx custom def exec -n <individual_assessment> -p <repo-path> -g file://.atx-config-<service-name>.yaml -x -t
```

**How Kiro generates the `additionalPlanContext`:**
1. Set `goal` from the portfolio config (defaults to `general-readiness` if missing or unrecognized)
2. Set `goal_context` from the portfolio config (if present)
3. Set `repo_type` from the per-repo config (only if explicitly specified — otherwise the transformation auto-detects)
4. Set `context` from the per-repo config (if present)
5. Merge preferences: start with global `preferences`, append per-repo `preferences`. If a value appears in both global `prefer` and per-repo `avoid`, remove it from `prefer` (per-repo `avoid` wins)
6. Set `priority` from the per-repo config (if present)
7. Set `tags` from the per-repo config (if present)

The `-x` (non-interactive) flag is mandatory — subagents run without human intervention. Kiro waits for all subagents to complete before proceeding.

> **Timeout Note:** Each `atx custom def exec` invocation is a long-running process (typically 5–15 minutes). Subagents MUST NOT poll, retry, or re-check repeatedly. After launching the command, wait patiently — do NOT check status in a loop or re-run the command. A single check after 10–15 minutes is sufficient. If the command appears to time out, check **once** whether the expected report file was written to `{repo}/agentic-readiness-assessment/` before reporting failure. The presence of the report file is the definitive success indicator, not the command's exit code or timing. Never retry a transformation that is still running.

Each assessment generates:
```
{repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md
```

### Step 2: Run Portfolio Assessment

After all subagents complete their individual assessments, Kiro generates a portfolio-level ATX configuration file and runs the portfolio transformation using the name from `transformation_definitions.portfolio_assessment`.

**Generated ATX config example** (`.atx-config-portfolio.yaml`):
```yaml
additionalPlanContext: |
  goal: "agentic-ai-enablement"
  goal_context: "Building customer-facing AI agents for support and order management"
  preferences:
    prefer: ["eks", "aurora", "bedrock"]
    avoid: ["self-managed-kafka"]
  
  Portfolio: ecommerce-platform
  Services Assessed: 4
  
  Service Inventory:
  - storefront-web (P0, ./services/storefront-web) — Tags: frontend, customer-facing
  - checkout-service (P0, ./services/checkout-service) — Tags: backend, payment
  - inventory-service (P1, ./services/inventory-service) — Tags: backend, data
  - infra-repo (P2, ./infrastructure) — repo_type: infrastructure-only
  
  Dependency Overrides:
  - storefront-web -> checkout-service (sync): Storefront calls Checkout REST API for order placement
  - checkout-service -> inventory-service (sync): Checkout validates inventory availability before order placement
```

```bash
atx custom def exec -n <portfolio_assessment> -p . -g file://.atx-config-portfolio.yaml -x -t
```

**How Kiro generates the portfolio `additionalPlanContext`:**
1. Set `goal` from the portfolio config (same value passed to individual assessments)
2. Set `goal_context` from the portfolio config (if present)
3. Set `preferences` from the global portfolio-level preferences (not merged with per-repo — global only)
4. Build the service inventory from all repositories in the config, including name, priority, path, tags, and repo_type where specified
5. Include `dependency_overrides` verbatim from the portfolio config

This generates:
```
agentic-readiness-assessment/{portfolio-name}-portfolio-agentic-readiness-report.md
```

### Step 3: Consolidate Reports

After the portfolio assessment completes, Kiro consolidates all reports into a single directory at the portfolio root for easy access and review.

**What Kiro does:**
1. Creates `agentic-readiness-assessment/` at the portfolio root (if it doesn't already exist from the portfolio assessment)
2. Copies each individual assessment report from `{repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md` into the root `agentic-readiness-assessment/` folder
3. The portfolio report is already at `agentic-readiness-assessment/{portfolio-name}-portfolio-agentic-readiness-report.md`
4. Cleans up temporary `.atx-config-*.yaml` files generated during the assessment

**Resulting structure:**
```
agentic-readiness-assessment/
├── service-a-agentic-readiness-report.md
├── service-b-agentic-readiness-report.md
├── service-c-agentic-readiness-report.md
└── my-platform-portfolio-agentic-readiness-report.md
```

### Step 4: Review Portfolio Report

The portfolio report provides:
- **Executive Dashboard** - Portfolio-wide readiness scores and trends
- **Service Dependency Map** - Visual representation of service relationships and coupling
- **Cross-Cutting Concerns** - Gaps affecting 3+ services that should be addressed portfolio-wide
- **4-Phase Modernization Roadmap** - Dependency-aware implementation plan
- **Integration Opportunities** - Shared services, event-driven architecture, API gateway patterns
- **Resource Allocation** - Team structure, skill gaps, training recommendations
- **Risk Analysis** - Portfolio-level risks with mitigation strategies

---

## Assessment Criteria Reference

1. **Infrastructure & Platform** (10 criteria)
   - Compute, databases, orchestration, messaging, IaC, CI/CD, API gateway, streaming, networking, auto-scaling

2. **Application Architecture** (13 criteria)
   - Languages, API docs, async/sync patterns, monolith vs microservices, response formats, workflows, idempotency, rate limiting, resilience, long-running processes, versioning, service discovery, AI frameworks

3. **Data Foundations** (11 criteria)
   - Vector databases, RAG, data sources, access patterns, unstructured data, schemas, data access layer, embedding freshness, DB versions, stored procedures

4. **Identity, Security & Governance** (10 criteria)
   - Secret management, IAM, identity propagation, audit logging, rate limits, PII redaction, human approval, encryption, API auth, centralized identity

5. **Operations & Observability** (12 criteria)
   - Distributed tracing, structured logging, automated evals, SLOs, rollback, LLM cost tracking, business metrics, anomaly detection, deployment strategy, integration testing, incident automation, observability governance

## Scoring Scale

| Score | Label | Meaning |
|-------|-------|---------|
| 4 | ✅ Agent-Ready | Fully meets criterion, no gaps |
| 3 | 🟡 Partial | Partially meets criterion, minor gaps |
| 2 | 🟠 Needs Work | Exists but significant gaps |
| 1 | ❌ Not Present | Missing entirely or inadequate |

## Output Structure

After consolidation, all reports are collected into a single folder at the portfolio root:

### Consolidated Output (Portfolio Root)

```
agentic-readiness-assessment/
├── {service-a}-agentic-readiness-report.md      ← copied from services/service-a/
├── {service-b}-agentic-readiness-report.md      ← copied from services/service-b/
├── {service-c}-agentic-readiness-report.md      ← copied from services/service-c/
└── {portfolio-name}-portfolio-agentic-readiness-report.md
    ├── Executive Dashboard
    ├── Portfolio Readiness Overview
    ├── Service Dependency Map
    ├── Cross-Cutting Concerns
    ├── 4-Phase Portfolio Roadmap
    ├── Integration Opportunities
    ├── Resource Allocation
    ├── Risk Analysis
    └── Service-by-Service Summary
```

### Individual Assessment Report (per repo, before consolidation)

```
{repo}/agentic-readiness-assessment/
└── {project-name}-agentic-readiness-report.md
    ├── Executive Summary
    ├── Top 5 Priorities
    ├── 3-Phase Roadmap
    ├── Learning Materials
    ├── Detailed Findings (56 criteria)
    └── Evidence Index
```

## Example Usage

### Basic Portfolio Assessment

```yaml
# portfolio-config.yaml
portfolio_name: "payment-platform"
goal: "general-readiness"

transformation_definitions:
  individual_assessment: "individual-aws-agentic-assessment"
  portfolio_assessment: "portfolio-agentic-assessment"

repositories:
  - name: "payment-gateway"
    path: "./services/payment-gateway"
    priority: "P0"
  - name: "fraud-detection"
    path: "./services/fraud-detection"
    priority: "P0"
  - name: "billing-service"
    path: "./services/billing"
    priority: "P1"
```

### Goal-Driven Portfolio with Preferences

```yaml
# portfolio-config.yaml
portfolio_name: "ecommerce-platform"
goal: "agentic-ai-enablement"
goal_context: "Building customer-facing AI agents for support and order management"

transformation_definitions:
  individual_assessment: "my-team-agentic-assessment"
  portfolio_assessment: "my-team-portfolio-assessment"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka", "oracle"]

repositories:
  - name: "storefront"
    path: "./services/storefront"
    priority: "P0"
    context: "Main customer-facing web application"
    preferences:
      avoid: ["microservices-decomposition"]  # Keep as monolith
      
  - name: "checkout"
    path: "./services/checkout"
    priority: "P0"
    context: "Handles payments and order processing"
    preferences:
      prefer: ["dynamodb"]
      avoid: ["rds"]
      
  - name: "inventory"
    path: "./services/inventory"
    priority: "P1"
    tags: ["backend", "data"]

  - name: "infra-repo"
    path: "./infrastructure"
    repo_type: "infrastructure-only"
    priority: "P2"

dependency_overrides:
  - source: "storefront"
    target: "checkout"
    type: "sync"
    description: "REST API calls for order placement"
  - source: "checkout"
    target: "inventory"
    type: "sync"
    description: "Validates inventory availability before order placement"
```

## Best Practices

1. **Set a clear goal** - Choose the goal that best matches the customer's modernization objective. Use `goal_context` to provide additional specificity
2. **Run individual assessments first** - Portfolio assessment requires completed individual reports
3. **Always use `-x -t` flags** - Non-interactive (`-x`) is mandatory for parallel execution at scale; trust all tools (`-t`) avoids prompts blocking subagents
4. **Use preferences wisely** - Guide recommendations with `prefer`/`avoid` arrays to match your constraints
5. **Document dependencies** - Use `dependency_overrides` for implicit dependencies
6. **Set priorities where helpful** - P0 for critical services, P1 for high priority, P2 for medium (optional)
7. **Specify repo_type when obvious** - If a repo is clearly infrastructure-only or a library, set `repo_type` to skip irrelevant criteria
8. **Review cross-cutting concerns** - Address portfolio-wide gaps before service-specific work
9. **Follow dependency order** - Modernize upstream services before downstream dependents
10. **Validate configuration** - Use the JSON schema to validate your portfolio-config.yaml before running
11. **Leverage parallel subagents** - Kiro runs individual assessments concurrently, so larger portfolios don't linearly increase execution time

---

## Troubleshooting

### Individual Assessment Fails

**Problem:** Transformation fails on a specific repository

**Solutions:**
1. Check AWS Transform CLI is installed: `atx --version`
2. Verify transformation is available: `atx custom def list | grep <your-transformation-name>`
3. Ensure the names in `transformation_definitions` match exactly what you published
4. Ensure you're in the correct repository directory
5. Check repository has required files (source code, build configs)
6. Run in interactive mode without `-x -t` flags to see detailed errors

### Portfolio Assessment Can't Find Individual Reports

**Problem:** Portfolio assessment reports missing individual assessments

**Solutions:**
1. Verify individual assessments completed successfully
2. Check report paths match configuration:
   ```
   {repo}/agentic-readiness-assessment/{project-name}-agentic-readiness-report.md
   ```
3. Ensure `path` in portfolio-config.yaml points to correct repository directories
4. Verify repository names in config match actual directory names

### Configuration Validation Errors

**Problem:** Portfolio configuration is rejected

**Solutions:**
1. Validate against schema:
   ```bash
   # Using a JSON schema validator
   ajv validate -s portfolio-config.schema.json -d portfolio-config.yaml
   ```
2. Check required fields:
   - `portfolio_name` is a non-empty string
   - `goal` is one of: `agentic-ai-enablement`, `cloud-native-modernization`, `cost-optimization`, `general-readiness`
   - `transformation_definitions` has both `individual_assessment` and `portfolio_assessment`
   - Each repository has `name` and `path`
   - Paths are relative to portfolio root
3. Check optional field formats:
   - `preferences.prefer` and `preferences.avoid` are string arrays
   - `repo_type` (if specified) is one of: `application`, `infrastructure-only`, `deployment-cicd`, `monorepo`, `library`
   - `priority` (if specified) is one of: `P0`, `P1`, `P2`
4. Review `portfolio-config.example.yaml` for correct format

> **Note:** V2 config is a breaking change from V1. Old configs using `global_transformation_preferences`, `transformation_options`, `exclusions`, `metadata`, or nested constraint objects (`database_constraints`, `deployment_constraints`, etc.) must be migrated to the new simplified format.

### Preferences Not Applied

**Problem:** Recommendations ignore specified preferences

**Solutions:**
1. Check that `preferences` uses the correct format: `prefer` and `avoid` as string arrays
2. Verify per-repo preferences are merging correctly with global preferences (per-repo `avoid` overrides global `prefer` for conflicts)
3. Remember preferences are guidance, not guarantees — some recommendations may still suggest avoided technologies if they're the best fit
4. Review generated report's recommendations against your preference configuration

### AWS Transform CLI Not Found

**Problem:** `atx: command not found`

**Solutions:**
1. Install AWS Transform CLI: https://docs.aws.amazon.com/transform/
2. Verify installation: `atx --version`
3. Check PATH includes AWS Transform CLI binary location
4. Restart terminal after installation

### ATX Command Timeout

**Problem:** `atx custom def exec` command times out or appears to hang

**Context:** This is expected behavior. Individual assessments typically take 5–15 minutes per repository. Portfolio assessments can take even longer depending on the number of services.

**Solutions:**
1. **Check for the output report first** — the command may have completed successfully even if the shell timed out:
   ```bash
   # For individual assessments:
   ls {repo}/agentic-readiness-assessment/*-agentic-readiness-report.md
   
   # For portfolio assessments:
   ls agentic-readiness-assessment/*-portfolio-agentic-readiness-report.md
   ```
2. If the report file exists, the assessment succeeded — no need to re-run
3. If the report file is missing, re-run the command with a longer timeout or no timeout
4. For very large repositories, consider running assessments individually in interactive mode (without `-x`) to monitor progress

---

## Limitations

- Minimum 2 services required for portfolio assessment
- Individual assessments must complete successfully before portfolio assessment
- Dependency detection is based on code analysis and may miss implicit dependencies
- Transformation preferences guide recommendations but don't guarantee specific solutions
- Assessment quality depends on code completeness and documentation availability

---

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
