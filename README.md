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
│   └── custom/                     # custom TDs (atx custom def exec) — you invoke these by name
│       ├── eba-execution-plan-generator/          # EBA execution plan TD
│       ├── bpmn-opportunity-analysis/             # BAO: per-repo BPMN agentic opportunity analysis
│       ├── portfolio-bpmn-opportunity-analysis/   # portfolio BAO aggregation
│       └── bridge-analysis/                        # ARA↔MOD bridge (agentic-readiness dividend)
├── orchestrator/
│   ├── SKILL.md                    # Claude/agent skill: full ARA/MODA/EBA workflow
│   └── references/                 # getting-started, ct-workflow, execution-plan, troubleshooting
├── tools/
│   └── bpmn-analyzer/              # deterministic BPMN preprocessor (BAO input; Python)
├── scripts/
│   └── publish-td.sh               # Publish a TD folder to the ATX registry
├── demo-scripts/                    # Full demo harness (setup, reset, live-discovery)
│   ├── 00-full-setup.sh            # Bake env: source + discovery + ARA + MODA + export (~45 min)
│   ├── 00-push-repos.sh            # [remote mode only] push the pre-baked repos to a GitHub org
│   ├── 01-live-discovery-push.sh   # Live beat: new repo appears (3 → 4)
│   ├── 02-reset-live-discovery.sh  # Reset for rehearsal
│   └── 99-full-reset.sh            # Nuke everything
├── harness/                         # change-impact harness — advisory, never blocks a merge
│   ├── DESIGN.md                    # scored dimensions + the reasoning behind each step
│   ├── usecases.yaml                # fixture matrix + coverage axes + expectations
│   ├── fixtures/                    # test/demo repos the harness runs the TDs over
│   │   ├── portfolio/              # 10 synthetic legacy repos (also the demo portfolio)
│   │   └── monolith/               # PHP test fixture
│   ├── golden/                      # committed baseline reports each MR diffs against
│   ├── should-run.sh                # 0. gate: deterministic run|skip path check (no LLM)
│   ├── run-fixtures.sh              # 1. publish the edited TD + atx custom def exec
│   ├── skill_table.py               # parses the TDs' severity tables; 2. severity gate
│   ├── diff-reports.py              # 3. D1–D5 delta + safety alerts -> impact.json
│   ├── score-reports.py             # 4. groundedness vs source -> compare.json
│   ├── judge.py                     # 5. LLM-as-judge -> verdict.json (the only LLM call)
│   ├── validate-contract.py         # schema guardrail: structural JSON-contract check
│   ├── post-mr-comment.sh           # 6. advisory MR comment
│   └── tests/                       # offline test suite (no AWS, no LLM)
├── examples/
│   └── atx-config-exec-plan.yaml   # Example EBA config
└── README.md
```

## Components

### `definitions/managed/` — the 4 managed TDs

The AWS-managed definitions that run **inside** `atx ct` — you never invoke them by name. `atx ct analysis run --type agentic-readiness` runs the per-repo ARA TD across every discovered repo, then the portfolio ARA TD aggregates the results (same pattern for `--type modernization-readiness`). The two portfolio TDs load `references/program-library.md` (the AWS Program & GTM Library) at runtime to produce engagement-program recommendations. See [`definitions/managed/README.md`](definitions/managed/README.md).

### `definitions/custom/` — the custom TDs

Custom TDs run via `atx custom def exec` (not `atx ct analysis run`) because they consume report/model artifacts as input and produce planning or opportunity outputs rather than per-repo findings. You invoke each by name. The table below is the pointer — each TD's `SKILL.md` holds the full `additionalPlanContext` field reference in its Step 0.

| TD | What it does | Required input | How to run |
|---|---|---|---|
| [`eba-execution-plan-generator`](definitions/custom/eba-execution-plan-generator/SKILL.md) | Dependency-aware modernization roadmap from ARA and/or MODA output | ≥1 portfolio report + human planning context (team size, timeline) | `atx custom def exec -n eba-execution-plan-generator -p . -g file://atx-config-exec-plan.yaml -x -t` (details below) |
| [`bpmn-opportunity-analysis`](definitions/custom/bpmn-opportunity-analysis/SKILL.md) | BAO — classifies BPMN 2.0 process steps as agentic-AI opportunities (category + autonomy) | JSON from `tools/bpmn-analyzer/run_analysis.py` (`analysis_report_path`) | Run the analyzer first, then `atx custom def exec -n bpmn-opportunity-analysis -p . -g file://bao-config.yaml -x -t` |
| [`portfolio-bpmn-opportunity-analysis`](definitions/custom/portfolio-bpmn-opportunity-analysis/SKILL.md) | Aggregates per-repo BAO reports into a portfolio opportunity view | Auto-discovers per-repo BAO reports (no config required) | `atx custom def exec -n portfolio-bpmn-opportunity-analysis -p . -x -t` |
| [`bridge-analysis`](definitions/custom/bridge-analysis/SKILL.md) | Cross-references portfolio ARA + MOD — shared remediation, modernization dividend, dedup | Portfolio ARA report + portfolio MOD report paths + `portfolio_name` | `atx custom def exec -n bridge-analysis -p . -g file://bridge-config.yaml -x -t` |

The EBA TD is the richest — it needs at least one portfolio report (ARA-only, MODA-only, or both; both gets cross-dependency detection) plus human planning inputs the agent can't infer from code. The other three take only file-path pointers or auto-discover their inputs.

`ct` writes per-repo artifacts into the repo working trees; portfolio output lands only in the source-scoped run tree. The authoritative location of every report is the `report_paths` map on the analysis record (`atx ct analysis get --id <id> --json`), which has sharp edges — markdown-only paths, portfolio `.json`/`.html` in exactly one place, removed `list-artifacts`/`get-artifact` subcommands. [`orchestrator/SKILL.md`](orchestrator/SKILL.md) has the full three-location table and current commands.

The EBA `-g` config (`additionalPlanContext`) carries the execution constraints — team size and timeline (required), plus optional budget, parallel capacity, compliance deadlines, and sequencing overrides. See [`examples/atx-config-exec-plan.yaml`](examples/atx-config-exec-plan.yaml) for the annotated template and [`orchestrator/references/execution-plan.md`](orchestrator/references/execution-plan.md) for the flow that generates it.

### `orchestrator/` — the agent skill

A Claude/agent skill ([`orchestrator/SKILL.md`](orchestrator/SKILL.md)) that turns an agent into the orchestrator for the full workflow: source setup → discovery → ARA/MODA analysis → findings → Execution Plan. Reference docs in [`orchestrator/references/`](orchestrator/references/) are read on demand (getting started, ct workflow, execution plan, troubleshooting).

Install it for Claude Code, then start Claude from the project root:

```bash
mkdir -p ~/.claude/skills/ara-moda-orchestrator
cp -R orchestrator/SKILL.md orchestrator/references ~/.claude/skills/ara-moda-orchestrator/

# re-copy after pulling; a stale copy confidently calls commands that no longer exist
diff -q orchestrator/SKILL.md ~/.claude/skills/ara-moda-orchestrator/SKILL.md \
  && echo "skill is current" || echo "STALE — re-copy"
```

The skill carries the verified `atx ct` behavior — which commands were removed, when a run is genuinely finished, and where reports actually land. Those are the places an agent working from the CLI's own help text gets it wrong, usually in ways that look like success.

### `scripts/publish-td.sh` — publishing TDs

Publishes a TD folder to the ATX registry. The TD name is derived from the folder basename; the description is extracted from the SKILL.md frontmatter (or the first heading of `transformation_definition.md`).

```bash
# Publish
./scripts/publish-td.sh definitions/custom/eba-execution-plan-generator

# Save as draft
./scripts/publish-td.sh definitions/managed/portfolio-agentic-readiness-analysis --draft
```

Requires the `atx` CLI and `AWS_REGION=us-east-1` (or a supported region).

### `harness/` — the change-impact harness

A rubric edit is a one-line diff whose blast radius is a whole portfolio of reports. Reading
the diff tells you what the text now says; it does not tell you that `AUTH-Q5` was emitted as a
BLOCKER on 6 of 12 reference reports, above its documented severity. The harness answers that
question mechanically: it re-runs the **edited** TD over fixture repos, diffs the resulting
reports against a committed baseline, and posts an advisory verdict on the MR.

**Every job is `allow_failure: true` — the harness never blocks a merge.** It is a reviewer aid,
not a gate. The only LLM call is the judge, spent once at the very end; the run/skip decision is
a deterministic `git diff`, not a model.

Fixtures live under `harness/fixtures/`: `portfolio/` holds the 10 synthetic legacy repos (also
the source the demo scripts discover), `monolith/` is a PHP fixture for local runs. The
committed baseline each MR diffs against — a full set of per-repo ARA/MOD reports and portfolio
roll-ups — is `harness/golden/`. See [`harness/README.md`](harness/README.md) for the pipeline
diagram and setup, and [`harness/DESIGN.md`](harness/DESIGN.md) for the scored dimensions and
the reasoning behind each step.

> Automation runs on the internal GitLab instance only, where the AWS credentials live. GitHub
> stays open for issues and PRs but carries no CI.

### `examples/` — EBA config

`examples/atx-config-exec-plan.yaml` is a sample EBA `additionalPlanContext` config.

## Quickstart

Prerequisites: AWS credentials (`aws sts get-caller-identity`), the ATX CLI (see the [official install docs](https://docs.aws.amazon.com/transform/)), Node.js 22+, and the `AWSTransformCustomFullAccess` managed policy.

```bash
# Check the CLI version (needs ≥ 3.9.0)
atx --version

# Region: only us-east-1 resolves for the definition/credential endpoint
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1

# No server to start — analyses run in-process. This is just a health check.
atx ct status --health

# Add a local source (absolute path to a parent directory containing repos,
# each of which must contain a .git directory for discovery to find it)
atx ct source add --name my-portfolio --provider local --path $(pwd)/services

# Discover repositories
atx ct discovery scan --source my-portfolio

# Run ARA (per-repo + portfolio aggregation), then poll
atx ct analysis run --type agentic-readiness --source my-portfolio
atx ct analysis get --id <analysis-id>

# Run MODA (after ARA — do not run both concurrently)
atx ct analysis run --type modernization-readiness --source my-portfolio

# Inspect findings
atx ct findings count --by severity --json
atx ct findings list --json
```

> `atx ct server` is deprecated and hidden — never start it; it blocks the shell on `:8081` and is not required. A hidden `--wait` does exist on `analysis run`, but polling is preferable in agent workflows. Both are covered in [`orchestrator/SKILL.md`](orchestrator/SKILL.md), which is the current source of truth for CLI behavior.

The [`orchestrator/SKILL.md`](orchestrator/SKILL.md) skill walks an agent through the same workflow interactively.

## Contributing

**Changing a rubric (add / remove / re-score a question)?** Start at
[`docs/contributing/`](docs/contributing/README.md) — the front-door guide to TD anatomy, the
change playbook, and the invariants that break silently.

For repo-level PR mechanics see [CONTRIBUTING.md](CONTRIBUTING.md). Use the GitHub issue
templates to report bugs or suggest enhancements.

## Security

See [SECURITY.md](SECURITY.md). Treat analysis reports as confidential — they contain architecture details.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
