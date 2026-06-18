# Portfolio Analysis Orchestrator

A [Kiro](https://kiro.dev) Power that orchestrates **Agentic Readiness Analysis (ARA)** and **Modernization Readiness Analysis (MODA)** using [AWS Transform Continuous Modernization](https://docs.aws.amazon.com/transform/) (`atx ct`), with optional **Execution Plan** generation via `atx custom def exec`.

## Prerequisites

| Requirement | Verification |
|---|---|
| AWS credentials | `aws sts get-caller-identity` |
| AWS Transform CLI | `atx --version` ([install](https://docs.aws.amazon.com/transform/): `curl -fsSL https://transform-cli.awsstatic.com/install.sh \| bash`) |
| Node.js 22+ | `node --version` |
| `AWSTransformCustomFullAccess` managed policy | Attached to your IAM user/role |
| [Kiro IDE](https://kiro.dev) | For using the Power (optional for CLI-only use) |

## Quick Start

```bash
# Start the ct server (runs on localhost:8081)
atx ct server &

# Add a local source (absolute path to parent directory containing repos)
atx ct source add --name my-portfolio --provider local --path $(pwd)/services

# Discover repositories
atx ct discovery scan --source my-portfolio

# Run ARA
atx ct analysis run --type agentic-readiness --source my-portfolio --wait

# Run MODA
atx ct analysis run --type modernization-readiness --source my-portfolio --wait

# Inspect findings
atx ct findings list --json
```

## Source Providers

| Provider | Key flags | Example |
|---|---|---|
| `local` | `--path <parent-dir>` | `--provider local --path /home/user/services` |
| `github` | `--org <org> --token <PAT>` | `--provider github --org my-org --token ghp_xxx` |
| `gitlab` | `--org <group> --token <PAT>` | `--provider gitlab --org my-group --token glpat-xxx` |
| `bitbucket` | `--org <workspace> --token <token>` | `--provider bitbucket --org my-ws --token xxx` |

Local sources require an **absolute path** to a parent directory containing repos as subdirectories (each with a `.git` folder).

## Analysis Types

| Type | Description |
|---|---|
| `agentic-readiness` | Evaluates whether systems are ready to be safely called by AI agents |
| `modernization-readiness` | Scans for cloud-native maturity gaps and maps to AWS modernization pathways |
| `custom` | Run custom transformation definitions (supports `-g`/`--configuration` flag) |

Additional built-in types: `tech-debt-quick`, `tech-debt-comprehensive`, `security`.

## Integration Paths

### 1. Kiro Power (recommended)

The Power reads [`orchestrator/POWER.md`](orchestrator/POWER.md), guides you through the full workflow (source setup → discovery → analysis → findings → execution plan), handles long-running analyses with polling, and suggests next steps.

```
Run the portfolio analysis orchestrator on my services
```

### 2. MCP Server (agent integrations)

```bash
atx ct mcp
```

Exposes 41 tools over stdio (default) or HTTP. Implements MCP protocol `2024-11-05`. Suitable for embedding in agent frameworks, IDE extensions, or custom toolchains.

### 3. CLI (scripts and CI/CD)

Use `atx ct` commands directly as shown in Quick Start. Add `--json` for machine-readable output.

## Execution Plan

The Execution Plan (EBA) generates a dependency-aware modernization roadmap from ARA and MODA report artifacts. It still runs via `atx custom def exec` (not `atx ct analysis run`) because it consumes exported JSON artifacts and produces a roadmap document rather than findings.

```bash
atx custom def exec -n portfolio-execution-plan-generation -p . -g file://atx-config-exec-plan.yaml -x -t
```

See [`orchestrator/steering/execution-plan.md`](orchestrator/steering/execution-plan.md) for full details.

## Repository Structure

```
├── orchestrator/
│   ├── POWER.md                    # Main Kiro Power (workflow, safety contracts, UX)
│   └── steering/
│       ├── getting-started.md      # Prerequisites and first-run walkthroughs
│       ├── ct-workflow.md          # End-to-end ct workflow reference
│       ├── execution-plan.md       # EBA generation guide
│       └── troubleshooting.md      # Common errors and fixes
├── definitions/
│   └── portfolio-execution-plan-generation/
│       └── SKILL.md                # Execution Plan TD source
├── examples/
│   ├── atx-config-exec-plan.yaml   # Example EBA config
│   ├── fixtures/monolith/          # PHP test fixture
│   └── reports/full-analysis/      # Example generated reports
├── services/                       # Sample repos for analysis
└── README.md
```

## Example Reports

The `examples/reports/full-analysis/` directory contains a complete set of generated reports from a real analysis run — including per-service reports, portfolio roll-ups, and the unified execution plan.

## Live Dashboard

Interactive portfolio dashboards (ARA + MODA): **https://d2fplme21ym2t.cloudfront.net**

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Use the GitHub issue templates to report bugs or suggest enhancements.

## Security

See [SECURITY.md](SECURITY.md) for security guidelines. Treat analysis reports as confidential — they contain architecture details.

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [Kiro IDE](https://kiro.dev)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
