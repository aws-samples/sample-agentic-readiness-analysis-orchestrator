---
name: "agentic-assessment-orchestrator"
displayName: "Agentic Assessment Orchestrator"
description: "Orchestrate comprehensive agentic readiness assessments and modernization assessments across multiple repositories with portfolio-level analysis, dependency mapping, and coordinated roadmaps."
keywords: ["agentic", "assessment", "portfolio", "modernization", "aws", "readiness", "transformation", "dependencies"]
author: "AWS"
---

# Agentic Assessment Orchestrator

## Overview

This Knowledge Base Power turns Kiro into an orchestrator for running comprehensive assessments across your entire service portfolio. Kiro reads your `portfolio-config.yaml`, handles repository cloning when needed, classifies each repository, and coordinates AWS Transform Custom transformations based on the configured `assessment_type`:

- **Agentic Readiness Assessment (ARA)** — 49 questions across 8 sections using BLOCKER/RISK/INFO severity scoring. Evaluates whether systems are safe for autonomous AI agent integration.
- **Modernization Readiness Assessment (MOD)** — 37 questions across 5 sections using 1-4 scale scoring. Evaluates cloud architecture maturity and identifies modernization pathways.

The `assessment_type` field in `portfolio-config.yaml` controls which assessments run:
- `agentic-readiness` → ARA path only
- `modernization` → MOD path only
- `full` → both ARA and MOD paths in parallel

For each path, Kiro spawns parallel subagents (one per repository) for individual assessments, then runs the corresponding portfolio TD to aggregate results.

The transformation definition names are configurable in `portfolio-config.yaml` via the `transformation_definitions` section — use whatever names you published to your AWS Transform registry.

**How Kiro Orchestrates:**
- Parses `portfolio-config.yaml` to discover all repositories, their configuration, the `assessment_type`, `context`, `agent_scope`, `preferences`, and the transformation definition names
- Validates the `assessment_type` value — must be one of `agentic-readiness`, `modernization`, `full`; errors if missing or invalid (no default — assessment_type is required)
- Classifies each repository using the repo type decision tree (or uses the user-provided `repo_type` override from config)
- Validates per-repo fields: `name` and `path` required; `priority`, `context`, `preferences`, `repo_type`, `tags` optional
- Clones repositories automatically when `repository_url` is provided and the local `path` doesn't exist
- Routes by `assessment_type`:
  - `agentic-readiness` → generates ARA ATX configs per repo, spawns ARA subagents, then runs Portfolio ARA TD
  - `modernization` → generates MOD ATX configs per repo, spawns MOD subagents, then runs Portfolio MOD TD
  - `full` → generates both ARA and MOD ATX configs per repo (2 subagents per repo), then runs both portfolio TDs
- ARA ATX configs contain: `repo_type`, `agent_scope`, `context`, `priority`, `tags` — NO preferences
- MOD ATX configs contain: `repo_type`, `context`, `priority`, `tags`, merged `preferences` (global + per-repo with conflict resolution) — NO agent_scope
- Spawns parallel subagents to run `atx custom def exec -n <td_name> -g file://<generated-config> -x -t` concurrently
- Waits for all individual assessments to complete
- Generates portfolio-level ATX configs:
  - Portfolio ARA: `context`, service inventory, `dependency_overrides`
  - Portfolio MOD: `context`, `preferences`, service inventory, `dependency_overrides`
- Runs portfolio TDs to generate aggregated reports
- Consolidates ARA reports into `agentic-readiness-assessment/` folder and MOD reports into `modernization-assessment/` folder at the portfolio root — cleans up temporary `.atx-config-*.yaml` files

> All `atx` commands MUST use `-x` (non-interactive) and `-t` (trust all tools) flags since assessments run at scale without human intervention.

> **⏱ Long-Running Commands — Timeout Handling:** `atx custom def exec` commands are long-running operations that typically take **5–15 minutes per repository** depending on codebase size. These commands **will likely exceed default shell timeouts**. Subagents MUST NOT hang waiting for output or assume the command failed just because it took a long time. Instead, subagents should:
> 1. Launch the `atx` command with an appropriate timeout (or no timeout)
> 2. **Do NOT poll, retry, or re-check repeatedly.** After launching the command, wait patiently. Do not check status in a loop or re-run the command. A single check after a reasonable wait (10–15 minutes) is sufficient.
> 3. If the command times out or appears to hang, check **once** whether the assessment report file was generated at the expected output path
> 4. Validate success by checking for the existence of the output report file: `{repo}/agentic-readiness-assessment/{project-name}-ara-report.md` (for ARA) or `{repo}/modernization-assessment/{project-name}-mod-report.md` (for MOD)
> 5. If the report exists, treat the assessment as successful regardless of the command's exit behavior
> 6. Only report failure if the report file is missing AND the command returned a clear error
> 7. **Never retry a transformation that is still running.** Running duplicate `atx` processes against the same repo wastes resources and can cause conflicts.

**What You Get:**
- Assessment routing driven by `assessment_type` — run ARA, MOD, or both
- Automatic repo type classification with user override support
- Parallel subagent execution per repo for fast portfolio-wide assessment
- Cross-cutting analysis across the portfolio (blockers for ARA, score-based concerns for MOD)
- Configurable preferences to steer MOD technology recommendations
- Consolidated reports organized by assessment type

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
     agentic_readiness: "your-ara-td-name"
     modernization: "your-mod-td-name"
     portfolio_agentic_readiness: "your-portfolio-ara-td-name"
     portfolio_modernization: "your-portfolio-mod-td-name"
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

Create `portfolio-config.yaml` defining which services to assess, the assessment type, and any technology preferences:

```yaml
portfolio_name: "my-platform"
assessment_type: "full"
context: "Building customer-facing AI agents for support and order management"
agent_scope: "write-enabled"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

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
1. Parse `portfolio-config.yaml` — read `assessment_type`, `context`, `agent_scope`, `preferences`, `transformation_definitions`, `repositories`, and `dependency_overrides`
2. Validate the `assessment_type` value:
   - Must be one of: `agentic-readiness`, `modernization`, `full`
   - If missing or invalid → error (assessment_type is required, no default)
3. Classify each repository using the repo type decision tree (see Repo Type Classification below), or use the user-provided `repo_type` override
4. Validate per-repo fields: `name` and `path` are required; `priority`, `context`, `preferences`, `repo_type`, `tags`, `repository_url`, `report_path` are optional
5. Clone any repositories where `repository_url` is provided and `path` doesn't exist yet
6. Route by `assessment_type`:
   - **`agentic-readiness`**: For each repo, generate an ARA ATX config (repo_type, agent_scope, context, priority, tags — NO preferences). Spawn parallel subagents running the ARA TD. After completion, generate Portfolio ARA ATX config (context, service inventory, dependency_overrides) and run Portfolio ARA TD.
   - **`modernization`**: For each repo, generate a MOD ATX config (repo_type, context, priority, tags, merged preferences — NO agent_scope). Spawn parallel subagents running the MOD TD. After completion, generate Portfolio MOD ATX config (context, preferences, service inventory, dependency_overrides) and run Portfolio MOD TD.
   - **`full`**: Generate both ARA and MOD configs per repo (2 subagents per repo). Run both paths in parallel. After completion, run both portfolio TDs.
7. Consolidate reports:
   - ARA reports → `agentic-readiness-assessment/` folder
   - MOD reports → `modernization-assessment/` folder
   - Clean up temporary `.atx-config-*.yaml` files

### 3. Or Run Manually Step by Step

**ARA individual assessment (repeat for each repo):**
```bash
cd ./services/my-service
atx custom def exec -n <your-ara-td-name> -p . -g file://atx-config-ara.yaml -x -t
```

Where `atx-config-ara.yaml` contains the ARA `additionalPlanContext` (NO preferences):
```yaml
additionalPlanContext: |
  repo_type: "application"
  agent_scope: "write-enabled"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  priority: "P0"
  tags: ["monolith", "php"]
```

**MOD individual assessment (repeat for each repo):**
```bash
cd ./services/my-service
atx custom def exec -n <your-mod-td-name> -p . -g file://atx-config-mod.yaml -x -t
```

Where `atx-config-mod.yaml` contains the MOD `additionalPlanContext` (NO agent_scope):
```yaml
additionalPlanContext: |
  repo_type: "application"
  context: "Legacy PHP e-commerce app running on EC2 with MySQL"
  preferences:
    prefer: ["eks", "aurora", "bedrock", "dynamodb"]
    avoid: ["self-managed-kafka", "rds"]
  priority: "P0"
  tags: ["monolith", "php"]
```

**Portfolio ARA assessment (after all individual ARA assessments):**
```bash
atx custom def exec -n <your-portfolio-ara-td-name> -p . -g file://atx-portfolio-ara-config.yaml -x -t
```

Where `atx-portfolio-ara-config.yaml` contains:
```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  
  Portfolio: my-platform
  Services assessed: 2
  
  Service inventory:
  - service-a (P0, ./services/service-a) — Tags: monolith, php — repo_type: application
  - service-b (P1, ./services/service-b) — Tags: backend, inventory — repo_type: application
  
  Dependency overrides:
  - service-a -> service-b (sync): REST API calls for inventory checks
```

**Portfolio MOD assessment (after all individual MOD assessments):**
```bash
atx custom def exec -n <your-portfolio-mod-td-name> -p . -g file://atx-portfolio-mod-config.yaml -x -t
```

Where `atx-portfolio-mod-config.yaml` contains:
```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  preferences:
    prefer: ["eks", "aurora", "bedrock"]
    avoid: ["self-managed-kafka"]
  
  Portfolio: my-platform
  Services assessed: 2
  
  Service inventory:
  - service-a (P0, ./services/service-a) — Tags: monolith, php — repo_type: application
  - service-b (P1, ./services/service-b) — Tags: backend, inventory — repo_type: application
  
  Dependency overrides:
  - service-a -> service-b (sync): REST API calls for inventory checks
```

> Always use `-x` (non-interactive) and `-t` (trust all tools) when running at scale. Note: these commands are long-running (5–15 min each). If a command times out, check for the output report file before assuming failure.

---

## Portfolio Configuration

### Basic Configuration

Create a `portfolio-config.yaml` file to define which repositories to assess, the assessment type, and any technology preferences. Kiro will parse this file to orchestrate the assessment workflow. See `portfolio-config.example.yaml` for a complete example.

**Minimum Configuration:**

```yaml
portfolio_name: "my-platform"
assessment_type: "agentic-readiness"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

repositories:
  - name: "service-a"
    path: "./services/service-a"
  - name: "service-b"
    path: "./services/service-b"
```

**With Preferences and Repository Cloning:**

```yaml
portfolio_name: "my-platform"
assessment_type: "full"
context: "Building customer-facing AI agents for support and order management"
agent_scope: "write-enabled"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

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
assessment_type: "modernization"
context: "Decomposing monolith into containerized microservices for EKS"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

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

### Assessment Type Configuration

The `assessment_type` field controls which assessment paths are executed. It is required — there is no default.

| Assessment Type | Description |
|----------------|-------------|
| `agentic-readiness` | Run ARA only — evaluates agentic readiness with BLOCKER/RISK/INFO scoring (49 questions, 8 sections) |
| `modernization` | Run MOD only — evaluates cloud architecture maturity with 1-4 scale scoring (37 questions, 5 sections) |
| `full` | Run both ARA and MOD in parallel — produces both sets of reports |

**Assessment Type Validation:**
- If `assessment_type` is missing → error (required field)
- If `assessment_type` is not one of the 3 valid values → error
- The `context` free-text field is optional and provides additional framing for recommendations (e.g., "Building a customer support agent that needs access to order and inventory data"). It replaces the old `goal_context` field and is passed to all TDs.
- The `agent_scope` field is optional (enum: `read-only`, `write-enabled`) and is ARA-only — the Power passes it only to ARA ATX configs. It controls conditional BLOCKER severity in the ARA TD.

### Repo Type Classification

The Power classifies each repository before spawning subagents. The classified `repo_type` determines which questions are marked N/A in both ARA and MOD TDs. Classification is performed once per repo — the same value is written to both ARA and MOD ATX configs.

**User Override:** If `repo_type` is specified in the portfolio config for a repository, the Power uses that value directly and skips auto-detection.

**Auto-Detection Decision Tree:**

```
🔍 Scan Repo
    │
    ▼
┌─────────────────────────┐
│ repo_type in config?     │
│                          │
│  YES → Use config value  │
│  NO  → Continue ▼        │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Has source code?         │
│ (.java, .py, .ts, .js,  │
│  .go, .cs, .rb, .php,   │
│  .rs, etc.)              │
│                          │
│  YES → ▼ (source path)  │
│  NO  → ▼ (no-source)    │
└──┬──────────────┬───────┘
   │              │
   ▼              ▼
SOURCE PATH    NO-SOURCE PATH
   │              │
   ▼              ▼
┌──────────┐  ┌──────────────────┐
│ Multiple │  │ IaC files only?  │
│ services │  │ (.tf, CFN, CDK,  │
│ w/ sep.  │  │  Helm, Kustomize)│
│ build    │  │                  │
│ configs? │  │ YES → infra-only │
│          │  │ NO  → ▼          │
│ YES →    │  └────────┬─────────┘
│ monorepo │           │
│          │           ▼
│ NO → ▼   │  ┌──────────────────┐
└──┬───────┘  │ Deploy configs?  │
   │          │ (Dockerfile,     │
   ▼          │  docker-compose, │
┌──────────┐  │  K8s manifests,  │
│ Has      │  │  CI/CD pipelines)│
│ entry    │  │                  │
│ point?   │  │ YES → deployment │
│ (main,   │  │        -config   │
│ index,   │  │ NO  → application│
│ app.*)   │  │        (default) │
│          │  └──────────────────┘
│ YES →    │
│ applic.  │
│          │
│ NO →     │
│ library  │
└──────────┘
```

**Repo Type Values:**

| repo_type | Description | When Detected |
|-----------|-------------|---------------|
| `application` | Deployable application with source code and entry point | Source code + entry point (also the default fallback) |
| `monorepo` | Multiple services with separate build configurations | Source code + multiple service dirs + separate build configs |
| `library` | Shared library/package without deployable entry point | Source code + package manifest but no deployable entry point |
| `infrastructure-only` | Only IaC files, no application source code | No source code, only IaC files (.tf, CloudFormation, CDK, Helm, Kustomize) |
| `deployment-config` | Only deployment/CI/CD configuration files | No source code, only deploy configs (Dockerfile, docker-compose, K8s manifests, CI/CD pipelines) |

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

**Preference Merging:** Per-repo `prefer`/`avoid` arrays are appended to global arrays. If a value appears in both global `prefer` and per-repo `avoid`, the per-repo `avoid` wins (more specific overrides less specific). Preferences are MOD-only — the Power includes merged preferences only in MOD ATX configs (individual and portfolio), never in ARA configs.

### Configuration Schema

The full configuration schema is available in `portfolio-config.schema.json`. Key sections:

- **portfolio_name** (required): Name identifier for the portfolio
- **assessment_type** (required): One of `agentic-readiness`, `modernization`, `full`
- **context** (optional): Free-text context for framing recommendations (replaces old `goal_context`)
- **agent_scope** (optional): One of `read-only`, `write-enabled` — ARA-only, controls conditional BLOCKER severity
- **transformation_definitions** (required): Names of the AWS Transform definitions to use
  - `agentic_readiness` (required): Name for per-repository ARA assessments
  - `modernization` (required): Name for per-repository MOD assessments
  - `portfolio_agentic_readiness` (required): Name for portfolio ARA aggregation
  - `portfolio_modernization` (required): Name for portfolio MOD aggregation
- **preferences** (optional): Global technology/pattern preferences (MOD-only — ignored for ARA configs)
  - `prefer` (optional): String array of preferred technologies/patterns
  - `avoid` (optional): String array of technologies/patterns to avoid
- **repositories** (required): List of services to assess
  - `name` (required): Service identifier
  - `path` (required): Local path to repository
  - `repository_url` (optional): Git URL — Kiro clones if `path` doesn't exist
  - `priority` (optional): P0 (critical), P1 (high), P2 (medium)
  - `context` (optional): Free-text description of the service
  - `preferences` (optional): Per-repo preference overrides (same `prefer`/`avoid` format) — MOD-only
  - `repo_type` (optional): Override auto-detection — one of `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`
  - `tags` (optional): String array of tags for categorization
  - `report_path` (optional): Custom output path for the assessment report
- **dependency_overrides** (optional): Manual dependency declarations
  - `source` (required): Source service name
  - `target` (required): Target service name
  - `type` (required): Dependency type (e.g., `sync`, `async`, `shared_db`, `shared_infra`)
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
# atx-config-ara.yaml (ARA — NO preferences)
additionalPlanContext: |
  repo_type: "application"
  agent_scope: "write-enabled"
  context: "Legacy Java monolith running on EC2"
  priority: "P0"
  tags: ["monolith", "java"]
```

```yaml
# atx-config-mod.yaml (MOD — NO agent_scope)
additionalPlanContext: |
  repo_type: "application"
  context: "Legacy Java monolith running on EC2"
  preferences:
    prefer: ["eks", "fargate"]
    avoid: ["serverless"]
  priority: "P0"
  tags: ["monolith", "java"]
```

```bash
atx custom def exec -n my-ara-assessment -p ./services/checkout -g file://atx-config-ara.yaml -x -t
atx custom def exec -n my-mod-assessment -p ./services/checkout -g file://atx-config-mod.yaml -x -t
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
│     config file      │  and extracts assessment_type, context,
│                      │  preferences, repos, and dependencies
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  2. Validate         │  assessment_type must be one of:
│     assessment_type  │  agentic-readiness | modernization | full
│     & config fields  │  Error if missing or invalid
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
│  4. Classify repos   │  For each repo, run decision tree
│                      │  (or use config repo_type override).
│                      │  Same value for ARA + MOD configs.
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  5. Generate ATX     │  Route by assessment_type:
│     config files     │  ARA configs: repo_type, agent_scope,
│                      │    context, priority, tags
│                      │  MOD configs: repo_type, context,
│                      │    priority, tags, merged preferences
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│  6. Run individual assessments IN PARALLEL            │
│                                                       │
│  agentic-readiness:                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ ARA      │ │ ARA      │ │ ARA      │ ...          │
│  │ repo-a   │ │ repo-b   │ │ repo-c   │              │
│  └──────────┘ └──────────┘ └──────────┘              │
│                                                       │
│  modernization:                                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ MOD      │ │ MOD      │ │ MOD      │ ...          │
│  │ repo-a   │ │ repo-b   │ │ repo-c   │              │
│  └──────────┘ └──────────┘ └──────────┘              │
│                                                       │
│  full: both ARA + MOD per repo (2 subagents each)     │
└─────────────────────┬───────────────────────────────┘
                      │  (wait for all to complete)
                      ▼
┌─────────────────────┐
│  7. Generate         │  Portfolio ARA config: context,
│     portfolio        │    service inventory, dep overrides
│     configs          │  Portfolio MOD config: context,
│                      │    preferences, service inventory,
│                      │    dep overrides
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  8. Run portfolio    │  ARA path → Portfolio ARA TD
│     assessments      │  MOD path → Portfolio MOD TD
│                      │  Full → both
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  9. Consolidate      │  ARA reports → agentic-readiness-assessment/
│     reports          │  MOD reports → modernization-assessment/
│                      │  Clean up temp .atx-config-*.yaml files
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 10. Review reports   │  Reports organized by assessment type
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

Kiro spawns subagents per repository from `portfolio-config.yaml`. The number of subagents per repo depends on `assessment_type`: one for `agentic-readiness` or `modernization`, two for `full`. For each repository, Kiro first classifies the repo type (or uses the config override), then generates temporary ATX configuration files with the appropriate fields for each assessment path.

**Generated ARA ATX config example** (`.atx-config-checkout-service-ara.yaml`):
```yaml
additionalPlanContext: |
  repo_type: "application"
  agent_scope: "write-enabled"
  context: "Monolithic checkout handling payments and orders"
  priority: "P0"
  tags: ["backend", "payment", "critical-path"]
```

**Generated MOD ATX config example** (`.atx-config-checkout-service-mod.yaml`):
```yaml
additionalPlanContext: |
  repo_type: "application"
  context: "Monolithic checkout handling payments and orders"
  preferences:
    prefer: ["eks", "aurora", "bedrock", "dynamodb"]
    avoid: ["self-managed-kafka", "serverless"]
  priority: "P0"
  tags: ["backend", "payment", "critical-path"]
```

Each subagent then runs the appropriate assessment transformation concurrently:

```bash
# ARA subagent (using transformation_definitions.agentic_readiness):
atx custom def exec -n <agentic_readiness> -p <repo-path> -g file://.atx-config-<service-name>-ara.yaml -x -t

# MOD subagent (using transformation_definitions.modernization):
atx custom def exec -n <modernization> -p <repo-path> -g file://.atx-config-<service-name>-mod.yaml -x -t
```

**How Kiro generates the ARA `additionalPlanContext`:**
1. Set `repo_type` from classification (auto-detected or config override)
2. Set `agent_scope` from the portfolio config (if present; defaults to `read-only` if not specified)
3. Set `context` from the per-repo config (if present)
4. Set `priority` from the per-repo config (if present)
5. Set `tags` from the per-repo config (if present)
6. Do NOT include `preferences` — ARA configs never contain preferences

**How Kiro generates the MOD `additionalPlanContext`:**
1. Set `repo_type` from classification (same value as ARA — classified once per repo)
2. Set `context` from the per-repo config (if present)
3. Merge preferences: start with global `preferences`, append per-repo `preferences`. If a value appears in both global `prefer` and per-repo `avoid`, remove it from `prefer` (per-repo `avoid` wins)
4. Set `priority` from the per-repo config (if present)
5. Set `tags` from the per-repo config (if present)
6. Do NOT include `agent_scope` — MOD configs never contain agent_scope

The `-x` (non-interactive) flag is mandatory — subagents run without human intervention. Kiro waits for all subagents to complete before proceeding.

> **Timeout Note:** Each `atx custom def exec` invocation is a long-running process (typically 5–15 minutes). Subagents MUST NOT poll, retry, or re-check repeatedly. After launching the command, wait patiently — do NOT check status in a loop or re-run the command. A single check after 10–15 minutes is sufficient. If the command appears to time out, check **once** whether the expected report file was written before reporting failure. The presence of the report file is the definitive success indicator, not the command's exit code or timing. Never retry a transformation that is still running.

Each ARA assessment generates:
```
{repo}/agentic-readiness-assessment/{project-name}-ara-report.md
```

Each MOD assessment generates:
```
{repo}/modernization-assessment/{project-name}-mod-report.md
```

### Step 2: Run Portfolio Assessments

After all subagents complete their individual assessments, Kiro generates portfolio-level ATX configuration files and runs the portfolio TDs. Which portfolio TDs run depends on `assessment_type`.

**Generated Portfolio ARA ATX config example** (`.atx-config-portfolio-ara.yaml`):
```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  
  Portfolio: ecommerce-platform
  Services Assessed: 4
  
  Service Inventory:
  - storefront-web (P0, ./services/storefront-web) — Tags: frontend, customer-facing — repo_type: application
  - checkout-service (P0, ./services/checkout-service) — Tags: backend, payment — repo_type: application
  - inventory-service (P1, ./services/inventory-service) — Tags: backend, data — repo_type: application
  - infra-repo (P2, ./infrastructure) — repo_type: infrastructure-only
  
  Dependency Overrides:
  - storefront-web -> checkout-service (sync): Storefront calls Checkout REST API for order placement
  - checkout-service -> inventory-service (sync): Checkout validates inventory availability before order placement
```

**Generated Portfolio MOD ATX config example** (`.atx-config-portfolio-mod.yaml`):
```yaml
additionalPlanContext: |
  context: "Building customer-facing AI agents for support and order management"
  preferences:
    prefer: ["eks", "aurora", "bedrock"]
    avoid: ["self-managed-kafka"]
  
  Portfolio: ecommerce-platform
  Services Assessed: 4
  
  Service Inventory:
  - storefront-web (P0, ./services/storefront-web) — Tags: frontend, customer-facing — repo_type: application
  - checkout-service (P0, ./services/checkout-service) — Tags: backend, payment — repo_type: application
  - inventory-service (P1, ./services/inventory-service) — Tags: backend, data — repo_type: application
  - infra-repo (P2, ./infrastructure) — repo_type: infrastructure-only
  
  Dependency Overrides:
  - storefront-web -> checkout-service (sync): Storefront calls Checkout REST API for order placement
  - checkout-service -> inventory-service (sync): Checkout validates inventory availability before order placement
```

```bash
# Portfolio ARA (using transformation_definitions.portfolio_agentic_readiness):
atx custom def exec -n <portfolio_agentic_readiness> -p . -g file://.atx-config-portfolio-ara.yaml -x -t

# Portfolio MOD (using transformation_definitions.portfolio_modernization):
atx custom def exec -n <portfolio_modernization> -p . -g file://.atx-config-portfolio-mod.yaml -x -t
```

**How Kiro generates the Portfolio ARA `additionalPlanContext`:**
1. Set `context` from the portfolio config (if present) — free-text framing for recommendations
2. Build the service inventory from all repositories in the config, including name, priority, path, tags, and repo_type
3. Include `dependency_overrides` verbatim from the portfolio config
4. Do NOT include `preferences`, `agent_scope`, or `goal`

**How Kiro generates the Portfolio MOD `additionalPlanContext`:**
1. Set `context` from the portfolio config (if present) — free-text framing for recommendations
2. Set `preferences` from the global portfolio-level preferences (not merged with per-repo — global only)
3. Build the service inventory from all repositories in the config, including name, priority, path, tags, and repo_type
4. Include `dependency_overrides` verbatim from the portfolio config
5. Do NOT include `agent_scope` or `goal`

Portfolio ARA generates:
```
agentic-readiness-assessment/{portfolio-name}-portfolio-ara-report.md
```

Portfolio MOD generates:
```
modernization-assessment/{portfolio-name}-portfolio-mod-report.md
```

### Step 3: Consolidate Reports

After the portfolio assessments complete, Kiro consolidates all reports into organized directories at the portfolio root for easy access and review.

**What Kiro does:**

For `agentic-readiness` or `full` assessment_type:
1. Creates `agentic-readiness-assessment/` at the portfolio root (if it doesn't already exist)
2. Copies each individual ARA report from `{repo}/agentic-readiness-assessment/{project-name}-ara-report.md` into the root `agentic-readiness-assessment/` folder
3. The portfolio ARA report is already at `agentic-readiness-assessment/{portfolio-name}-portfolio-ara-report.md`

For `modernization` or `full` assessment_type:
1. Creates `modernization-assessment/` at the portfolio root (if it doesn't already exist)
2. Copies each individual MOD report from `{repo}/modernization-assessment/{project-name}-mod-report.md` into the root `modernization-assessment/` folder
3. The portfolio MOD report is already at `modernization-assessment/{portfolio-name}-portfolio-mod-report.md`

Finally:
4. Cleans up temporary `.atx-config-*.yaml` files generated during the assessment

**Resulting structure (full assessment_type):**
```
agentic-readiness-assessment/
├── service-a-ara-report.md
├── service-b-ara-report.md
├── service-c-ara-report.md
└── my-platform-portfolio-ara-report.md

modernization-assessment/
├── service-a-mod-report.md
├── service-b-mod-report.md
├── service-c-mod-report.md
└── my-platform-portfolio-mod-report.md
```

### Step 4: Review Portfolio Reports

Reports are generated by the TDs — see the individual TD documentation for full output details.

- **ARA Portfolio Report**: Readiness distribution, cross-cutting blockers/risks, service-by-service summary
- **MOD Portfolio Report**: Score overview, cross-cutting concerns, dependency-aware roadmap, pathway aggregation, service-by-service summary

---

## Assessment Criteria Reference

The TDs define the full question sets, scoring rubrics, pathways, and report templates. The Power only needs to know:

- **ARA**: 49 questions, 8 sections, BLOCKER/RISK/INFO scoring, readiness profiles
- **MOD**: 37 questions, 5 sections, 1-4 scale scoring, 7 pathways

See the individual TDs for full details on questions, scoring rubrics, pathway triggers, and report content.

## Output Structure

After consolidation, reports are organized by assessment type at the portfolio root:

```
agentic-readiness-assessment/
├── {service-a}-ara-report.md
├── {service-b}-ara-report.md
└── {portfolio-name}-portfolio-ara-report.md

modernization-assessment/
├── {service-a}-mod-report.md
├── {service-b}-mod-report.md
└── {portfolio-name}-portfolio-mod-report.md
```

Individual reports (before consolidation) are generated at:
- ARA: `{repo}/agentic-readiness-assessment/{project-name}-ara-report.md`
- MOD: `{repo}/modernization-assessment/{project-name}-mod-report.md`

## Example Usage

### ARA-Only Portfolio Assessment

```yaml
# portfolio-config.yaml
portfolio_name: "payment-platform"
assessment_type: "agentic-readiness"
agent_scope: "write-enabled"
context: "Evaluating payment services for autonomous agent integration"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

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

### MOD-Only Portfolio with Preferences

```yaml
# portfolio-config.yaml
portfolio_name: "ecommerce-platform"
assessment_type: "modernization"
context: "Modernizing legacy e-commerce platform for cloud-native architecture"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

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

### Full Assessment (ARA + MOD)

```yaml
# portfolio-config.yaml
portfolio_name: "fintech-platform"
assessment_type: "full"
context: "Building AI-powered financial advisory agents while modernizing infrastructure"
agent_scope: "read-only"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka"]

repositories:
  - name: "advisory-engine"
    path: "./services/advisory"
    priority: "P0"
    context: "Core financial advisory logic"
  - name: "portfolio-tracker"
    path: "./services/portfolio"
    priority: "P1"
    tags: ["backend", "data"]
  - name: "shared-infra"
    path: "./infrastructure"
    repo_type: "infrastructure-only"
    priority: "P2"
```

## Best Practices

1. **Choose the right assessment_type** — Use `agentic-readiness` for agent safety evaluation, `modernization` for cloud maturity, or `full` for both
2. **Provide context** — Use the `context` field to frame recommendations for your specific situation
3. **Run individual assessments first** — Portfolio assessment requires completed individual reports
4. **Always use `-x -t` flags** — Non-interactive (`-x`) is mandatory for parallel execution at scale; trust all tools (`-t`) avoids prompts blocking subagents
5. **Use preferences wisely** — Guide MOD recommendations with `prefer`/`avoid` arrays to match your constraints (preferences are MOD-only)
6. **Set agent_scope for ARA** — Use `write-enabled` if agents will modify data; `read-only` for observation-only agents (affects conditional BLOCKER severity)
7. **Document dependencies** — Use `dependency_overrides` for implicit dependencies
8. **Set priorities where helpful** — P0 for critical services, P1 for high priority, P2 for medium (optional)
9. **Specify repo_type when obvious** — If a repo is clearly infrastructure-only or a library, set `repo_type` to skip irrelevant criteria and avoid misclassification
10. **Review cross-cutting concerns** — Address portfolio-wide gaps before service-specific work
11. **Follow dependency order** — Modernize upstream services before downstream dependents
12. **Validate configuration** — Use the JSON schema to validate your portfolio-config.yaml before running
13. **Leverage parallel subagents** — Kiro runs individual assessments concurrently, so larger portfolios don't linearly increase execution time

---

## Troubleshooting

### Individual Assessment Fails

**Problem:** Transformation fails on a specific repository

**Solutions:**
1. Check AWS Transform CLI is installed: `atx --version`
2. Verify transformation is available: `atx custom def list | grep <your-transformation-name>`
3. Ensure the names in `transformation_definitions` match exactly what you published (all 4 TD names must be correct)
4. Ensure you're in the correct repository directory
5. Check repository has required files (source code, build configs)
6. Run in interactive mode without `-x -t` flags to see detailed errors

### Portfolio Assessment Can't Find Individual Reports

**Problem:** Portfolio assessment reports missing individual assessments

**Solutions:**
1. Verify individual assessments completed successfully
2. Check report paths match configuration:
   ```
   # ARA reports:
   {repo}/agentic-readiness-assessment/{project-name}-ara-report.md
   
   # MOD reports:
   {repo}/modernization-assessment/{project-name}-mod-report.md
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
   - `assessment_type` is one of: `agentic-readiness`, `modernization`, `full`
   - `transformation_definitions` has all 4 TD names: `agentic_readiness`, `modernization`, `portfolio_agentic_readiness`, `portfolio_modernization`
   - Each repository has `name` and `path`
   - Paths are relative to portfolio root
3. Check optional field formats:
   - `context` is a free-text string
   - `agent_scope` (if specified) is one of: `read-only`, `write-enabled`
   - `preferences.prefer` and `preferences.avoid` are string arrays
   - `repo_type` (if specified) is one of: `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`
   - `priority` (if specified) is one of: `P0`, `P1`, `P2`
4. Review `portfolio-config.example.yaml` for correct format

> **Note:** V2 config is a breaking change from V1. Old configs using `goal`, `goal_context`, `individual_assessment`, `portfolio_assessment`, `deployment-cicd`, or nested constraint objects must be migrated to the new format. See the migration guide for details.

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
   # For individual ARA assessments:
   ls {repo}/agentic-readiness-assessment/*-ara-report.md
   
   # For individual MOD assessments:
   ls {repo}/modernization-assessment/*-mod-report.md
   
   # For portfolio ARA assessments:
   ls agentic-readiness-assessment/*-portfolio-ara-report.md
   
   # For portfolio MOD assessments:
   ls modernization-assessment/*-portfolio-mod-report.md
   ```
2. If the report file exists, the assessment succeeded — no need to re-run
3. If the report file is missing, re-run the command with a longer timeout or no timeout
4. For very large repositories, consider running assessments individually in interactive mode (without `-x`) to monitor progress

---

## Limitations

- Minimum 2 services required for portfolio assessment
- Individual assessments must complete successfully before portfolio assessment
- Dependency detection is based on code analysis and may miss implicit dependencies
- Transformation preferences guide MOD recommendations but don't guarantee specific solutions
- Preferences are MOD-only — they are not passed to ARA assessments
- Assessment quality depends on code completeness and documentation availability

---

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
