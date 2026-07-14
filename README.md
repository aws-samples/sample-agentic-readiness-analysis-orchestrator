# Agentic Readiness Analysis Orchestrator

Source of truth for the **Agentic Readiness Analysis (ARA)** / **Modernization Readiness Analysis (MODA)** analysis orchestrator, built on [AWS Transform Continuous Modernization](https://docs.aws.amazon.com/transform/) (`atx ct`). This repo holds the managed transformation definitions (TDs) that `ct` runs internally, the custom Execution Plan TD, and the agent skill that orchestrates the full workflow.

**`main` = prod.** What's merged to `main` in `definitions/managed/` is what the AWS Transform service runs.

## Repository Structure

```
├── definitions/
│   ├── managed/                    # 4 AWS-managed TDs (what `atx ct` runs internally; main = prod)
│   │   ├── README.md
│   │   ├── agentic-readiness-analysis/            # per-repo ARA
│   │   ├── modernization-readiness-analysis/      # per-repo MODA
│   │   ├── portfolio-agentic-readiness-analysis/  # portfolio ARA + program recs
│   │   │   └── references/program-library.md      # AWS Program & GTM Library (runtime-loaded)
│   │   └── portfolio-modernization-readiness-analysis/
│   │       └── references/program-library.md
│   └── custom/
│       └── eba-execution-plan-generator/   # EBA execution plan TD (atx custom def exec)
├── orchestrator/
│   ├── SKILL.md                    # Claude/agent skill: full ARA/MODA/EBA workflow
│   └── references/                 # getting-started, ct-workflow, execution-plan, troubleshooting
├── scripts/
│   └── publish-td.sh               # Publish a TD folder to the ATX registry
├── demo-scripts/                    # Full demo harness (setup, reset, live-discovery)
│   ├── 00-full-setup.sh            # Bake env: server + source + discovery + ARA + MODA (~45 min)
│   ├── 01-live-discovery-push.sh   # Live beat: new repo appears (3 → 4)
│   ├── 02-reset-live-discovery.sh  # Reset for rehearsal
│   └── 99-full-reset.sh            # Nuke everything
├── sample-legacy-portfolio/         # 10 synthetic legacy repos for demo/testing
├── examples/
│   ├── atx-config-exec-plan.yaml   # Example EBA config
│   ├── fixtures/monolith/          # PHP test fixture
│   └── reports/full-analysis/      # Sample generated reports
└── README.md
```

## Components

### `definitions/managed/` — the 4 managed TDs

The AWS-managed definitions that run **inside** `atx ct` — you never invoke them by name. `atx ct analysis run --type agentic-readiness` runs the per-repo ARA TD across every discovered repo, then the portfolio ARA TD aggregates the results (same pattern for `--type modernization-readiness`). The two portfolio TDs load `references/program-library.md` (the AWS Program & GTM Library) at runtime to produce engagement-program recommendations. See [`definitions/managed/README.md`](definitions/managed/README.md).

### `definitions/custom/` — the Execution Plan TD

`eba-execution-plan-generator` generates a dependency-aware modernization roadmap from the **output of ARA and/or MODA analyses**. It runs via `atx custom def exec` (not `atx ct analysis run`) because it consumes the report artifacts as input and produces a phased roadmap rather than findings.

**Input requirements — at least ONE portfolio report must exist** (ARA-only, MODA-only, or both; when both exist the plan covers both dimensions with cross-dependency detection):

```
<workspace>/
├── portfolio-agentic-readiness-analysis/
│   └── <portfolio>-ara-portfolio-report.json     ← from ct portfolio ARA analysis (optional*)
├── portfolio-modernization-readiness-analysis/
│   └── <portfolio>-mod-portfolio-report.json     ← from ct portfolio MODA analysis (optional*)
└── services/<repo-name>/
    ├── agentic-readiness-analysis/<repo>-ara-report.json       ← per-repo ARA (optional drill-down)
    └── modernization-readiness-analysis/<repo>-mod-report.json ← per-repo MODA (optional drill-down)
```

_*At least one of the two portfolio reports is required — the TD terminates with an error if neither is found. Per-repo reports are read only when deeper granularity is needed._

On **local sources**, `ct` writes these artifacts directly into the repo working trees during analysis. On **remote sources**, you must export them from the artifact store first:

```bash
# Export per-repo reports
atx ct analysis get-artifact --id <ara-id> --repo <slug> --name ara > services/<repo>/agentic-readiness-analysis/<repo>-ara-report.json
atx ct analysis get-artifact --id <moda-id> --repo <slug> --name mod > services/<repo>/modernization-readiness-analysis/<repo>-mod-report.json

# Export portfolio reports
atx ct analysis get-artifact --id <ara-id> --repo _portfolio_ara --name report > portfolio-agentic-readiness-analysis/<portfolio>-ara-portfolio-report.json
atx ct analysis get-artifact --id <moda-id> --repo _portfolio_mod --name report > portfolio-modernization-readiness-analysis/<portfolio>-mod-portfolio-report.json
```

**Running the EBA TD** (requires at least one portfolio report — ARA and/or MODA):

```bash
atx custom def exec -n eba-execution-plan-generator -p . -g file://atx-config-exec-plan.yaml -x -t
```

**The `-g` config (`additionalPlanContext`)** provides the execution constraints that shape how the roadmap is sequenced and phased. These are human inputs the TD cannot infer from code:

```yaml
# atx-config-exec-plan.yaml
additionalPlanContext: |
  portfolio_name: "my-platform"
  team_size: 8                          # engineers/teams available
  timeline_constraint: "12 months"      # total modernization timeline
  budget_constraint: "$1.2M"            # including training + infra
  parallel_capacity: 3                  # how many services modernized simultaneously
  compliance_requirements:              # hard deadlines (optional)
    - "SOC2 audit by 2026-03"
    - "PCI-DSS renewal Q4"
  sequencing_overrides:                 # business-priority ordering (optional)
    - "payments-service must complete first"
  service_inventory:                    # auto-populated from ct data
    - name: "payments-service"
      path: "/path/to/payments-service"
      priority: "P0"
      tags: ["java", "spring-boot"]
      findings_summary: {high: 4, medium: 12, low: 3}
  dependency_overrides:                 # inferred from cross-service findings
    - source: "payments-service"
      target: "user-service"
      type: "sync"
```

| Field | Required | Source |
|---|---|---|
| `team_size` | Yes | Human input |
| `timeline_constraint` | Yes | Human input |
| `budget_constraint` | No | Human input |
| `parallel_capacity` | No | Human input |
| `compliance_requirements` | No | Human input |
| `sequencing_overrides` | No | Human input |
| `service_inventory[]` | Yes | Auto-populated from `atx ct repository list` + `findings list` |
| `dependency_overrides[]` | No | Auto-inferred from cross-service findings |

The orchestrator skill ([`orchestrator/references/execution-plan.md`](orchestrator/references/execution-plan.md)) has the full interactive flow for generating this config with an agent. See also [`examples/atx-config-exec-plan.yaml`](examples/atx-config-exec-plan.yaml).

### `orchestrator/` — the agent skill

A Claude/agent skill ([`orchestrator/SKILL.md`](orchestrator/SKILL.md)) that turns an agent into the orchestrator for the full workflow: source setup → discovery → ARA/MODA analysis → findings → Execution Plan. Reference docs in [`orchestrator/references/`](orchestrator/references/) are read on demand (getting started, ct workflow, execution plan, troubleshooting).

### `scripts/publish-td.sh` — publishing TDs

Publishes a TD folder to the ATX registry. The TD name is derived from the folder basename; the description is extracted from the SKILL.md frontmatter (or the first heading of `transformation_definition.md`).

```bash
# Publish
./scripts/publish-td.sh definitions/custom/eba-execution-plan-generator

# Save as draft
./scripts/publish-td.sh definitions/managed/portfolio-agentic-readiness-analysis --draft
```

Requires the `atx` CLI and `AWS_REGION=us-east-1` (or a supported region).

### `examples/` — sample reports and fixtures

`examples/reports/full-analysis/` contains a complete set of generated reports from a real analysis run — per-service ARA/MODA reports, portfolio roll-ups, and the unified execution plan. `examples/fixtures/monolith/` is a PHP test fixture for local runs.

## Quickstart

Prerequisites: AWS credentials (`aws sts get-caller-identity`), the ATX CLI (`curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash`), Node.js 22+, and the `AWSTransformCustomFullAccess` managed policy.

```bash
# Start the ct server (localhost:8081)
atx ct server &

# Add a local source (absolute path to a parent directory containing repos)
atx ct source add --name my-portfolio --provider local --path $(pwd)/services

# Discover repositories
atx ct discovery scan --source my-portfolio

# Run ARA (per-repo + portfolio aggregation)
atx ct analysis run --type agentic-readiness --source my-portfolio --wait

# Run MODA (per-repo + portfolio aggregation)
atx ct analysis run --type modernization-readiness --source my-portfolio --wait

# Inspect findings
atx ct findings list --json
```

The [`orchestrator/SKILL.md`](orchestrator/SKILL.md) skill walks an agent through the same workflow interactively.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Use the GitHub issue templates to report bugs or suggest enhancements.

## Security

See [SECURITY.md](SECURITY.md). Treat analysis reports as confidential — they contain architecture details.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
