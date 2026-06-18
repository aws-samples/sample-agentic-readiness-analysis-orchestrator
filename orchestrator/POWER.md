---
name: "orchestrator"
displayName: "Portfolio Analysis Orchestrator"
description: "Orchestrate agentic readiness and modernization analyses across a service portfolio using AWS Transform Continuous Modernization (atx ct), with execution plan generation via atx custom."
keywords: ["agentic-readiness", "modernization-readiness-analysis", "portfolio-analysis", "ara", "mod", "aws-transform", "continuous-modernization"]
author: "AWS"
---

# Portfolio Analysis Orchestrator

## Overview

This Power turns Kiro into an orchestrator for running comprehensive analyses across your service portfolio using **AWS Transform Continuous Modernization** (`atx ct`). The ct server handles repository discovery, parallel execution, portfolio-level aggregation, findings management, and remediation natively — this Power provides the orchestration layer that connects ct's capabilities with execution plan generation.

### Supported Analyses

| Analysis | `atx ct` type | What it evaluates |
|---|---|---|
| **Agentic Readiness Analysis (ARA)** | `agentic-readiness` | 56 criteria across 5 categories: Infrastructure & Platform, Application Architecture, Data Foundations, Identity/Security/Governance, and Operations & Observability. Evaluates whether systems are ready to be safely called by AI agents. |
| **Modernization Readiness Analysis (MODA)** | `modernization-readiness` | Cloud modernization opportunity assessment. Evaluates readiness across infrastructure, application, data, security, and operations dimensions. Identifies candidates for containerization, serverless migration, and platform upgrades. |
| **Execution Plan (EBA)** | N/A — uses `atx custom def exec` | Generates a dependency-aware execution roadmap from ARA+MODA findings. Runs via the custom execution path using report artifacts as input. |

| `analysis_type` | What runs |
|---|---|
| `agentic-readiness` | ARA across all discovered repos (per-repo + portfolio aggregation) |
| `modernization` | MODA across all discovered repos (per-repo + portfolio aggregation) |
| `full` | ARA + MODA + Execution Plan |

### When to Use

- Planning agentic AI adoption across microservices
- Identifying shared infrastructure gaps and modernization opportunities
- Prioritizing modernization based on dependencies
- Tracking portfolio-wide readiness progress over time
- Generating execution roadmaps from analysis findings
- Continuous monitoring of tech debt and readiness regressions

---

## Available Steering Files

Read on demand based on what the user is asking. **Do not load all of these proactively** — pick the ones relevant to the current task.

| Steering file | When to read |
|---|---|
| `getting-started.md` | First-time setup: AWS credentials, ATX CLI installation, ct server lifecycle, source configuration |
| `ct-workflow.md` | Running analyses end-to-end: sources, discovery, analysis execution, findings management, artifact retrieval |
| `execution-plan.md` | Running the Execution Plan TD via `atx custom def exec` after ARA+MODA analyses are complete |
| `troubleshooting.md` | Errors, ct server issues, analysis failures, discovery problems, remediation errors |

To load a steering file: `Call action "readSteering" with powerName="orchestrator", steeringFile="<filename>"`

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  atx ct server (local, EC2, or Batch)                              │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ Source Mgmt  │  │  Discovery   │  │   Analysis Engine       │  │
│  │ github       │  │  repo scan   │  │   parallel execution    │  │
│  │ gitlab       │  │  .git detect │  │   portfolio aggregation │  │
│  │ bitbucket    │  │              │  │   artifact generation   │  │
│  │ local        │  │              │  │                         │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │   Findings   │  │  Remediation │  │  Reporting & Scheduling │  │
│  │   (results)  │  │  (PRs/MRs)   │  │  (HTML, EventBridge)    │  │
│  └──────────────┘  └──────────────┘  └─────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (report artifacts feed into)
┌────────────────────────────────────────────────────────────────────┐
│  atx custom def exec (Execution Plan generation only)              │
│  Reads report artifacts → produces dependency-aware roadmap        │
└────────────────────────────────────────────────────────────────────┘
```

---

## Core Workflow (High-Level)

```bash
# 1. Start the ct server
atx ct server &

# 2. Add a source (see "Source Providers" below for all options)
#    Local: uses --path    Remote: uses --org
atx ct source add --name my-portfolio --provider local --path ./services

# 3. Discover repositories
atx ct discovery scan --source my-portfolio

# 4. Run ARA analysis (per-repo + portfolio — handled by ct)
atx ct analysis run --type agentic-readiness --source my-portfolio --wait

# 5. Run MODA analysis (per-repo + portfolio — handled by ct)
atx ct analysis run --type modernization-readiness --source my-portfolio --wait

# 6. Inspect findings
atx ct findings list --json

# 7. (Optional) Retrieve report artifacts for EBA
atx ct analysis list-artifacts --id <analysis-id> --json
atx ct analysis get-artifact --id <analysis-id> --repo <repo-slug> --name ara

# 8. (Optional) Generate execution plan from report artifacts
atx custom def exec -n portfolio-execution-plan-generation -p . -g file://atx-config-exec-plan.yaml -x -t
```

---

## Source Providers

The ct server supports four source providers. Each tells ct where your repositories live.

### Local (for local directories)

```bash
atx ct source add --name my-local --provider local --path /absolute/path/to/parent-dir
```

- **`--path`** must point to a **parent directory** containing git repos as subdirectories
- Scanner looks for child directories that contain a `.git` folder
- Do NOT point to a single repo directly — point to the directory containing repos
- Example: if repos are at `./services/repo-a/`, `./services/repo-b/`, then `--path ./services`

> **Important:** Local sources use `--path`, NOT `--org`. The `--org` flag is only for remote providers (github, gitlab, bitbucket).

### GitHub (organizations)

```bash
atx ct source add --name my-github --provider github --org my-org --token ghp_xxxxxxxxxxxx
```

- Token needs `repo` scope (classic PAT)
- `--org` is the GitHub organization name
- Discovers all repos in the org

### GitLab (groups or users)

```bash
atx ct source add --name my-gitlab --provider gitlab --org my-group --token glpat-xxxxxxxxxxxx
```

- Token needs `api` scope
- `--org` is the GitLab group or username
- Supports self-hosted GitLab instances (pass `--url https://gitlab.example.com`)

### Bitbucket (workspaces or projects)

```bash
atx ct source add --name my-bitbucket --provider bitbucket --org my-workspace --token xxxxxxxxxxxx
```

- Cloud: `--org` is the workspace name
- Data Center: `--org` is the project key
- `--username` and `--email` flags available for Bitbucket auth
- Token needs read access to repos; write access for remediation PRs

### Managing Sources

```bash
atx ct source list              # List all configured sources (add --json for JSON)
atx ct source remove --name x   # Remove a source
```

---

## Analysis Types Reference

| Type | Description |
|---|---|
| `agentic-readiness` | AI agent integration readiness — 56 criteria, 5 categories |
| `modernization-readiness` | Cloud modernization opportunity assessment |
| `tech-debt-quick` | Fast metadata-only scan of package manifests |
| `tech-debt-comprehensive` | Deep code-level technical debt analysis |
| `security` | Security vulnerability and CVE detection (requires security agent setup) |
| `custom` | Run any transformation definition as an analysis: `--type custom --transformation-name <name>` |

### Configuration Limitation

The `-g`/`--configuration` flag on `atx ct analysis run` is **ONLY valid with `--type custom`**. Built-in analysis types (agentic-readiness, modernization-readiness, tech-debt-*, security) do not accept custom configuration — they use their own defaults.

---

## Report Artifacts

After analysis completes, report artifacts are stored in the ct server's artifact store — NOT written directly to the local filesystem.

### Listing artifacts

```bash
atx ct analysis list-artifacts --id <analysis-id> --json
```

### Retrieving artifact content

```bash
atx ct analysis get-artifact --id <analysis-id> --repo <repo-slug> --name ara
```

### Artifact names by analysis type

| Analysis type | Per-repo artifact name | Portfolio artifact repo key | Portfolio artifact name |
|---|---|---|---|
| `agentic-readiness` | `ara` | `_portfolio_ara` | `report` |
| `modernization-readiness` | `mod` | `_portfolio_mod` | `report` |

All artifacts have `"format": "markdown"` in the listing.

### Using artifacts for EBA

To feed report artifacts into the Execution Plan TD, retrieve them via `get-artifact` and save to files, or reference the analysis ID in your EBA config.

---

## Safety Contract: Execution Plan (EBA)

> The ct server handles all parallelism, git state, and portfolio aggregation for ARA/MODA. The following contract applies ONLY to the Execution Plan TD which runs via `atx custom def exec`.

1. **EBA runs only AFTER both ARA and MODA analyses show status `complete`** (confirmed by `atx ct analysis list` or `--wait` returning success).
2. **Verify report artifacts exist** via `atx ct analysis list-artifacts` before launching EBA.
3. **Issue exactly one `executeBash` call** for the EBA command with timeout 1800000 ms. Do not poll, background, or split.
4. **Do NOT run EBA concurrently with any `atx ct analysis run`** — the ct server and custom exec may conflict on git state.
5. After executeBash returns, verify the execution plan artifact exists before reporting success.

---

## Full CLI Reference

### Server & Status

| Command | Description |
|---|---|
| `atx ct server` | Start the continuous modernization server (default port 8081) |
| `atx ct server --port <port>` | Start on a custom port |
| `atx ct status` | View system status (sources, repos, analyses, findings, remediations) |
| `atx ct status --health` | Health check — prints "healthy" or "unhealthy" |

### Sources

| Command | Description |
|---|---|
| `atx ct source add --name <n> --provider local --path <p>` | Add local source |
| `atx ct source add --name <n> --provider github --org <o> --token <t>` | Add GitHub source |
| `atx ct source add --name <n> --provider gitlab --org <o> --token <t> [--url <u>]` | Add GitLab source |
| `atx ct source add --name <n> --provider bitbucket --org <o> --token <t> [--username <u>] [--email <e>]` | Add Bitbucket source |
| `atx ct source list [--json]` | List configured sources |
| `atx ct source remove --name <n>` | Remove a source |

### Discovery

| Command | Description |
|---|---|
| `atx ct discovery scan --source <name> [--path <override>]` | Discover repositories from a source |

### Repositories

| Command | Description |
|---|---|
| `atx ct repository list [--source <s>] [--language <l>] [--labels <l>] [--has-workflow <bool>] [--json]` | List repos |
| `atx ct repository get --id <id>` | Get single repo details |
| `atx ct repository update --id <id> --labels <l>` | Update repo labels |
| `atx ct repository delete --repo <slug> --source <s>` | Delete a repository |

### Analysis

| Command | Description |
|---|---|
| `atx ct analysis run --type <type> --source <name> [--repo <slug>] [--wait] [--telemetry <kv>]` | Run analysis |
| `atx ct analysis run --type custom --transformation-name <td> --source <name> [-g <config>] [--wait]` | Run custom TD as analysis |
| `atx ct analysis get --id <id>` | Get analysis details |
| `atx ct analysis list [--json] [--status <s>] [--type <t>] [--category <c>]` | List analyses |
| `atx ct analysis cancel --id <id>` | Cancel running analysis |
| `atx ct analysis delete --id <id>` | Delete an analysis |
| `atx ct analysis list-artifacts --id <id> [--json]` | List report artifacts for an analysis |
| `atx ct analysis get-artifact --id <id> --repo <repo> --name <name>` | Get artifact content |

### Findings

| Command | Description |
|---|---|
| `atx ct findings list [--json] [--source <s>] [--type <t>] [--severity <sev>] [--min-severity <sev>] [--status <s>] [--repo <r>] [--analysis-id <id>] [--fix-transform <name>]` | List findings |
| `atx ct findings get --id <id>` | Get single finding |
| `atx ct findings update --id <id> --status <s> [--reason "..."] [--notes "..."]` | Update a finding |
| `atx ct findings batch-update --ids <id1>,<id2> --status <s> [--reason "..."]` | Batch update |
| `atx ct findings delete --id <id>` | Delete dismissed/obsolete finding |

### Remediation

| Command | Description |
|---|---|
| `atx ct remediation create --ids <id1>,<id2> [--transformation-name <td>] [--name "..."] [--local] [--telemetry <kv>]` | Create remediation from findings |
| `atx ct remediation create --repo <slug> --source <s> --transformation-name <td> [-g <config>] [--name "..."] [--local]` | Create remediation for repo |
| `atx ct remediation list [--status <s>]` | List remediations |
| `atx ct remediation status --id <id>` | Check remediation status + PR/MR links |
| `atx ct remediation retry --id <id>` | Retry failed remediation |
| `atx ct remediation cancel --id <id>` | Cancel a remediation |
| `atx ct remediation delete --id <id>` | Delete a remediation |

### Setup

| Command | Description |
|---|---|
| `atx ct setup security-agent` | Provision security agent infrastructure |
| `atx ct setup security-agent --status` | Check security agent status |

### MCP Server

| Command | Description |
|---|---|
| `atx ct mcp` | Start MCP server exposing ATX Control Tower tools |
