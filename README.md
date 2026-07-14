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
│       └── portfolio-execution-plan-generation/   # EBA execution plan TD (atx custom def exec)
├── orchestrator/
│   ├── SKILL.md                    # Claude/agent skill: full ARA/MODA/EBA workflow
│   └── references/                 # getting-started, ct-workflow, execution-plan, troubleshooting
├── scripts/
│   └── publish-td.sh               # Publish a TD folder to the ATX registry
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

`portfolio-execution-plan-generation` generates a dependency-aware modernization roadmap (EBA) from the portfolio ARA/MODA report artifacts. It runs via `atx custom def exec` (not `atx ct analysis run`) because it consumes exported JSON artifacts and produces a roadmap document rather than findings:

```bash
atx custom def exec -n portfolio-execution-plan-generation -p . -g file://atx-config-exec-plan.yaml -x -t
```

### `orchestrator/` — the agent skill

A Claude/agent skill ([`orchestrator/SKILL.md`](orchestrator/SKILL.md)) that turns an agent into the orchestrator for the full workflow: source setup → discovery → ARA/MODA analysis → findings → Execution Plan. Reference docs in [`orchestrator/references/`](orchestrator/references/) are read on demand (getting started, ct workflow, execution plan, troubleshooting).

### `scripts/publish-td.sh` — publishing TDs

Publishes a TD folder to the ATX registry. The TD name is derived from the folder basename; the description is extracted from the SKILL.md frontmatter (or the first heading of `transformation_definition.md`).

```bash
# Publish
./scripts/publish-td.sh definitions/custom/portfolio-execution-plan-generation

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

For the full demo (reset-and-rebuild scripts, sample portfolio, local-first and GitHub modes), see the GitLab harness repo: `gitlab.aws.dev/agentic-readiness-assessment/agentic-test-harness-moda-ara`. The [`orchestrator/SKILL.md`](orchestrator/SKILL.md) skill walks an agent through the same workflow interactively.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Use the GitHub issue templates to report bugs or suggest enhancements.

## Security

See [SECURITY.md](SECURITY.md). Treat analysis reports as confidential — they contain architecture details.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
