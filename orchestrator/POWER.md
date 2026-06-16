---
name: "orchestrator"
displayName: "Portfolio Analysis Orchestrator"
description: "Orchestrate agentic readiness and modernization analyses across a service portfolio with reconciliation gates, dependency-aware roadmaps, and execution plan generation."
keywords: ["agentic-readiness", "modernization-readiness-analysis", "portfolio-analysis", "ara", "mod", "aws-transform"]
author: "AWS"
---

# Portfolio Analysis Orchestrator

## Overview

This Knowledge Base Power turns Kiro into an orchestrator for running comprehensive analyses across your service portfolio. Kiro reads `portfolio-config.yaml`, classifies repositories, spawns one subagent per repo, runs the appropriate AWS Transform transformations, aggregates results into portfolio-level reports, and optionally generates a portfolio-level execution plan.

Two analyses plus an execution plan TD are supported. The `analysis_type` field in `portfolio-config.yaml` controls which analyses run:

| Analysis | What it evaluates |
|---|---|
| **Modernization Readiness Analysis (MOD)** | 37 questions, 5 sections, 1-4 scale. Scans portfolios for cloud-native maturity gaps and maps findings to AWS modernization pathways. |
| **Agentic Readiness Analysis (ARA)** | 43 questions, 8 sections, BLOCKER/RISK/INFO scoring. Evaluates whether systems are ready to be safely called by AI agents — covering APIs, identity, state management, human-in-the-loop, and observability. |
| **Portfolio Execution Plan (EXEC)** | Unified. Consumes the portfolio MODA report AND/OR portfolio ARA report (at least one required) and produces a holistic engagement-level roadmap with modernization work streams (from MODA), agent-readiness work streams (from ARA), cross-dimension dependencies, phased timelines, cost estimates, risk registers, and decision points. |

| `analysis_type` | What runs |
|---|---|
| `agentic-readiness` | Per-repo ARA + Portfolio ARA |
| `modernization` | Per-repo MOD + Portfolio MOD |
| `full` | Both analyses |
| `execution-plan` | Portfolio Execution Plan — **requires:** at least one of `portfolio-modernization-readiness-analysis` OR `portfolio-agentic-readiness-analysis` complete. Consumes both when available for a unified plan with cross-dimension dependencies. |

Per-repo subagents run **in parallel across repos**. In `full` mode, each subagent runs its assigned TDs **sequentially within its repo** (ARA → MOD). After per-repo execution, a Reconciliation Gate verifies workspace state, then portfolio TDs run **strictly serially** with a gate between each.

### When to Use

- Planning agentic AI adoption across microservices
- Identifying shared infrastructure gaps
- Prioritizing modernization based on dependencies
- Tracking portfolio-wide readiness progress
- Generating executive-level portfolio reports
- Producing phased execution plans with cost estimates, risk registers, and work stream decomposition

---

## Available Steering Files

Read on demand based on what the user is asking. **Do not load all of these proactively** — pick the ones relevant to the current task.

| Steering file | When to read |
|---|---|
| `getting-started.md` | First-time setup, AWS credentials, ATX CLI installation, prerequisite checks |
| `portfolio-config.md` | Building or editing `portfolio-config.yaml`, understanding the schema, repo classification, preferences merging |
| `orchestration-workflow.md` | Actually running an analysis — Step 0 through Step 3, ATX config generation, subagent contract |
| `reconciliation-gate.md` | The mandatory gate between per-repo and portfolio TDs — Checks A (branch consolidation), B (path standardization), C (bundle completeness) |
| `manual-execution.md` | Running individual TDs by hand without the orchestrator (single-repo runs, debugging, partial reruns) |
| `troubleshooting.md` | Errors, missing reports, timeouts, subagent panic recovery, configuration validation issues |
| `execution-plan.md` | Generating a portfolio execution plan — engagement parameters, ATX config generation, TD invocation, output verification |
| `atx-cli-reference.md` | Quick reference for `atx` flags, configuration file format, common invocation patterns, recommended timeouts |

To load a steering file: `Call action "readSteering" with powerName="orchestrator", steeringFile="<filename>"`

---

## Three Critical Safety Contracts

> **These contracts apply to every run and MUST be followed. They are stated in this always-loaded file — not in steering files — because violating them produces silent data loss and corrupt reports. Every contract is a fix for a specific failure mode observed in production runs.**

### Contract 1: No-Polling Contract (subagents must not panic during long ATX runs)

`atx custom def exec` is long-running: 5-15 minutes for per-repo TDs, 15-30 minutes for portfolio TDs. Subagents have repeatedly broken correctness by becoming impatient mid-run, inspecting filesystem state before ATX has finished writing, then panicking and retrying. The retry corrupts state because two ATX processes against the same repo path produce divergent staging branches.

**The contract:**

1. **Issue exactly one `executeBash` call** for the ATX command, with the configured timeout (1200000 ms per-repo, 1800000 ms portfolio). Do not pre-launch, do not background, do not split.
2. **Do NOT call `ls`, `find`, `cat`, `grep`, or any filesystem inspection tool against the repo's analysis folders while ATX is running.** The agent's executeBash call IS the wait. There is no work to do until it returns.
3. **Do NOT read ATX log files or `~/.aws/atx/custom/...` paths during the run.** ATX writes incrementally; partial reads produce misleading state.
4. **Do NOT spawn a second subagent or a parallel executeBash to "check on" the first one.**
5. **Do NOT interpret stdout buffering pauses, "Thinking..." spinners, or quiet periods as failure.** ATX runs with no stdout output for minutes at a time; this is normal.
6. **Do exactly one filesystem check after executeBash returns** (success, error, or timeout). The `.md` presence is the authoritative success signal — all four artifacts are produced together or none are:
   ```bash
   ls {repo}/agentic-readiness-analysis/{slug}-ara-report.md 2>/dev/null     # ARA
   ls {repo}/modernization-readiness-analysis/{slug}-mod-report.md 2>/dev/null # MOD
   ```
7. If the `.md` file exists -> **SUCCESS**, regardless of executeBash exit code or timeout status.
8. If the `.md` file is missing AND executeBash returned a clear error -> **FAILURE** with the error.
9. If the `.md` file is missing AND executeBash timed out with no error -> **TIMEOUT**. Recommend manual re-run with extended timeout. Do NOT retry inside the subagent.
10. **Never retry a transformation that may still be running.**

**Recovery from panicked subagent:** If you observe a subagent making multiple filesystem inspections during what should be a single ATX wait, the run is compromised. Stop that subagent and re-launch the TD freshly. Do not try to salvage partial state from the panicked run.

### Contract 2: Per-Repo Serialization Rule (`full` mode)

Each ATX execution forks a per-execution staging branch (`atx-result-staging-<timestamp>-<id>`) by stashing+committing local changes onto that branch and then restoring the original branch. **Two ATX executions against the same repo path concurrently each fork their own staging branch from the same starting HEAD**, never see each other's commits, and produce divergent histories.

**The contract:**

- Within a single repository, analyses MUST run sequentially: ARA → MOD
- Across repositories, run subagents fully in parallel (one subagent per repo)
- **One subagent per repo, never more.** The subagent sequences its assigned TDs.

The serialization adds at most one TD's runtime to each repo (~10-15 minutes) but eliminates the entire class of staging-branch race conditions: lost artifacts, reports written to wrong nested paths (e.g., `monolith/services/monolith/...`), and merge conflicts on regenerated files.

**Per-portfolio branch isolation (recommended):** Before invoking the orchestrator on operator-owned repos, create a dedicated branch (`git checkout -b portfolio-run-<date>`). All ATX staging branches will fork from this branch. At the end you have a single isolated branch you can merge or delete as a unit.

### Contract 3: Portfolio TD Serialization

All portfolio TDs (Portfolio ARA, Portfolio MOD) execute against the same workspace root with `-p .`. They share a single git HEAD. Running two portfolio TDs concurrently triggers the same staging-branch divergence that Contract 2 prevents at the repo level.

**The contract:**

- Run portfolio TDs strictly serially in this order: **Portfolio ARA → Portfolio MOD**
- A **Reconciliation Gate** runs between each invocation (see `steering/reconciliation-gate.md` for Checks A/B/C)
- Abort the chain if any gate fails — do not proceed to the next portfolio TD with a corrupted workspace

The portfolio phase typically takes ~30 minutes for a full analysis with both portfolio TDs. This is the cost of correctness; do not optimize it away by parallelizing.

**Cross-repo per-repo subagents remain parallel** — only the portfolio aggregation step is serialized.

---

## How Kiro Orchestrates (High-Level)

Detailed step-by-step flow lives in `steering/orchestration-workflow.md`. Summary:

1. **Pre-flight (Step 0):** Verify AWS credentials, ATX CLI, TD existence in registry. Fail fast on any failure.
2. **Parse and validate `portfolio-config.yaml`:** analysis_type, repos, preferences, dependency_overrides, TD names.
3. **Classify each repo:** Apply the decision tree (or honor user-provided `repo_type` override).
4. **Clone missing repos:** For entries with `repository_url` and a non-existent `path`.
5. **Generate ATX configs:** Per-repo ARA (no preferences), per-repo MOD (no agent_scope, merged preferences). Portfolio configs include structured `service_inventory[]` and `dependency_overrides[]`.
6. **Per-repo execution (Contract 2):** One subagent per repo. Subagent runs its assigned TDs sequentially within the repo. All subagents in parallel across repos.
7. **Reconciliation Gate (Step 1.5):** Check A (branch consolidation), Check B (canonical paths — auto-rename and auto-move strays since Contract 2 makes their attribution unambiguous, ABORT only when >=2 strays exist for the same TD in one repo), Check C (four-artifact bundle completeness, `.json` mandatory). Abort before any portfolio TD if any check fails.
8. **Portfolio TDs (Contract 3):** Strictly serial — Portfolio ARA → Portfolio MOD — with a Reconciliation Gate between each.
9. **Consolidate reports:** Copy per-repo reports into top-level `agentic-readiness-analysis/`, `modernization-readiness-analysis/` folders. Clean up `.atx-config-*.yaml`.

> All `atx` commands MUST use `-x` (non-interactive) and `-t` (trust all tools) — analyses run at scale without human intervention. Always pass **absolute paths** to `-p` and `-g`; relative paths silently break across `executeBash` boundaries because each call starts a fresh shell. See `steering/atx-cli-reference.md` for full flag details and `steering/troubleshooting.md` for the path-corruption failure mode.

---

## Quick Start

### 1. Create `portfolio-config.yaml`

Minimum config to validate the toolchain:

```yaml
portfolio_name: "my-platform"
analysis_type: "full"
context: "Building customer-facing AI agents while modernizing legacy services"
agent_scope: "read-only"

transformation_definitions:
  agentic_readiness: "AWS/agentic-readiness-analysis"
  modernization: "AWS/modernization-readiness-analysis"
  portfolio_agentic_readiness: "AWS/portfolio-agentic-readiness-analysis"
  portfolio_modernization: "AWS/portfolio-modernization-readiness-analysis"

preferences:
  prefer: ["eks", "aurora", "bedrock"]
  avoid: ["self-managed-kafka"]

repositories:
  - name: "service-a"
    repository_url: "https://github.com/org/service-a.git"
    path: "./services/service-a"
    priority: "P0"
  - name: "service-b"
    path: "./services/service-b"
    priority: "P1"
```

For full schema and more examples, read `steering/portfolio-config.md`.

### 2. Create a Portfolio-Run Branch (recommended)

For each repo under your control:

```bash
git -C <repo_path> checkout -b portfolio-run-$(date +%Y%m%d)
```

ATX staging branches fork from this isolation branch. Cleanup is then a single merge or delete.

### 3. Ask Kiro to Run the Orchestrator

```
"Run the portfolio analysis orchestrator on portfolio-config.yaml"
```

Kiro will work through the orchestration workflow in `steering/orchestration-workflow.md`, enforcing all three safety contracts above.

For manual execution without the orchestrator, read `steering/manual-execution.md`.

---

## Output Structure

After a `full` run, the workspace contains:

```
agentic-readiness-analysis/
├── service-a-ara-report.{md,json,html,metadata.json}
├── service-b-ara-report.{md,json,html,metadata.json}
└── my-platform-portfolio-ara-report.{md,json,html,metadata.json}

modernization-readiness-analysis/
├── service-a-mod-report.{md,json,html,metadata.json}
├── service-b-mod-report.{md,json,html,metadata.json}
└── my-platform-portfolio-mod-report.{md,json,html,metadata.json}

```

### Four-Artifact Bundle

Every per-repo and portfolio analysis emits four files. JSON is authoritative on conflict.

| Artifact | Purpose |
|---|---|
| `{name}-report.md` | Richest-prose narrative (rubric quotes, BLOCKER remediation blocks, score tables, top gaps, decomposition strategy, pathway details, execution roadmap, risk register) |
| `{name}-report.json` | **Canonical machine-readable contract.** Consumed by the webapp dashboard and by portfolio TDs. |
| `{name}-report.html` | Single self-contained HTML — no external asset fetches at render time. Every value originates from the JSON. |
| `{name}-report.metadata.json` | Tiny sidecar carrying `{analysis_type, analysis_date, td_version}`. Same fields are also at the root of the main JSON under `metadata`. |

The Reconciliation Gate (Check C) treats `.json` as mandatory — portfolio TDs cannot aggregate without it.

---

## Best Practices

1. **Choose the right `analysis_type`** — ARA for agent safety, MOD for cloud maturity, `full` for both.
2. **Provide `context`** — Free-text portfolio context frames recommendations far better than letting the TD reason from code alone.
3. **Set `agent_scope` for ARA** — `write-enabled` for agents that modify data, `read-only` for observation-only. Affects conditional BLOCKER severity.
4. **Use `preferences` to steer MOD** — Global `prefer`/`avoid` arrays plus per-repo overrides. See `steering/portfolio-config.md` for merge rules.
5. **Specify `repo_type` when obvious** — Skip auto-detection for clearly-infrastructure repos (`infrastructure-only`) or libraries (`library`).
6. **Document dependencies** — Use `dependency_overrides[]` for implicit dependencies the orchestrator cannot infer from code analysis.
7. **Set priorities where helpful** — `P0` for critical services, `P1` for high priority, `P2` for medium. Optional but improves portfolio roadmap sequencing.
8. **Run individual analyses first** — Portfolio analyses require completed individual reports. The reconciliation gate enforces this, but configuring `analysis_type: full` is the simplest path.
9. **Create a portfolio-run branch first** — Prevents ATX staging branches from polluting `main`. Cleanup is one merge instead of many.
10. **Run the Reconciliation Gate manually if running TDs by hand** — Same Checks A/B/C apply. See `steering/reconciliation-gate.md`.
11. **Leverage cross-repo parallelism** — Kiro spawns one subagent per repository so larger portfolios scale near-linearly. Per-repo serialization within `full` mode is mandatory but adds at most one TD's runtime per repo.
12. **Address cross-cutting concerns first** — Portfolio reports surface gaps that affect multiple services. Fix those before per-service work.
13. **Follow dependency order in modernization** — Modernize upstream services before their downstream dependents.
14. **Validate config against the JSON schema** — `ajv validate -s portfolio-config.schema.json -d portfolio-config.yaml` before running.

---

## Troubleshooting

For all error scenarios — missing reports, ATX timeouts, panicked subagents, configuration errors, branch hygiene issues — read `steering/troubleshooting.md`.

Most common issues:
- **Reports missing -> Reconciliation Gate failure.** Reports may be at non-canonical paths or stranded on staging branches.
- **`.json` missing but `.md` exists -> mandatory abort.** Re-run that per-repo TD.
- **ATX timeout but report exists -> SUCCESS.** No-Polling Contract treats this as success regardless of executeBash exit status.
- **Subagent panic -> kill and re-launch.** Don't try to salvage partial state.

---

## Limitations

- Minimum 2 services for portfolio analysis
- Per-repo analyses must succeed before portfolio aggregation
- Dependency detection is code-analysis-based — declare implicit dependencies via `dependency_overrides[]`
- Preferences are guidance, not guarantees
- Preferences are MOD-only (silently ignored by ARA)
- Analysis quality depends on code completeness and documentation availability

---

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
