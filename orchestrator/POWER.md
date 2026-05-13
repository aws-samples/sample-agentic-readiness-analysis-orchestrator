---
name: "orchestrator"
displayName: "Portfolio Analysis Orchestrator"
description: "Orchestrate agentic readiness, modernization, and BPMN opportunity analyses across a service portfolio with reconciliation gates and dependency-aware roadmaps."
keywords: ["agentic-readiness", "modernization-analysis", "portfolio-analysis", "bpmn-opportunity", "ara", "mod", "aws-transform"]
author: "AWS"
---

# Portfolio Analysis Orchestrator

## Overview

This Knowledge Base Power turns Kiro into an orchestrator for running comprehensive assessments across your service portfolio. Kiro reads `portfolio-config.yaml`, classifies repositories, spawns one subagent per repo, runs the appropriate AWS Transform transformations, and aggregates results into portfolio-level reports.

Three assessments are supported. The `assessment_type` field in `portfolio-config.yaml` controls which run:

| Assessment | What it evaluates |
|---|---|
| **Agentic Readiness Analysis (ARA)** | 43 questions, 8 sections, BLOCKER/RISK/INFO scoring. Evaluates whether systems are safe for autonomous AI agent integration. |
| **Modernization Analysis (MOD)** | 37 questions, 5 sections, 1-4 scale. Evaluates cloud architecture maturity and identifies modernization pathways. |
| **BPMN Agentic Opportunity (BAO)** | Analyzes BPMN 2.0 process models to identify agentic candidates by reasoning complexity and data readiness. |

| `assessment_type` | What runs |
|---|---|
| `agentic-readiness` | Per-repo ARA + Portfolio ARA |
| `modernization` | Per-repo MOD + Portfolio MOD |
| `bpmn-opportunity` | Per-repo BAO + Portfolio BAO (only repos with `.bpmn` files) |
| `full` | All three, plus Bridge TD when `portfolio_bridge` is configured |

Per-repo subagents run **in parallel across repos**. In `full` mode, each subagent runs its assigned TDs **sequentially within its repo** (ARA → MOD → BAO). After per-repo execution, a Reconciliation Gate verifies workspace state, then portfolio TDs run **strictly serially** with a gate between each.

### When to Use

- Planning agentic AI adoption across microservices
- Identifying which business process steps should become agent-powered (BPMN opportunity)
- Identifying shared infrastructure gaps
- Prioritizing modernization based on dependencies
- Tracking portfolio-wide readiness progress
- Generating executive-level portfolio reports

---

## Available Steering Files

Read on demand based on what the user is asking. **Do not load all of these proactively** — pick the ones relevant to the current task.

| Steering file | When to read |
|---|---|
| `getting-started.md` | First-time setup, AWS credentials, ATX CLI installation, prerequisite checks |
| `portfolio-config.md` | Building or editing `portfolio-config.yaml`, understanding the schema, repo classification, preferences merging |
| `orchestration-workflow.md` | Actually running an assessment — Step 0 through Step 3, ATX config generation, subagent contract |
| `reconciliation-gate.md` | The mandatory gate between per-repo and portfolio TDs — Checks A (branch consolidation), B (path standardization), C (bundle completeness) |
| `manual-execution.md` | Running individual TDs by hand without the orchestrator (single-repo runs, debugging, partial reruns) |
| `troubleshooting.md` | Errors, missing reports, timeouts, subagent panic recovery, configuration validation issues |
| `atx-cli-reference.md` | Quick reference for `atx` flags, configuration file format, common invocation patterns, recommended timeouts |

To load a steering file: `Call action "readSteering" with powerName="orchestrator", steeringFile="<filename>"`

---

## Three Critical Safety Contracts

> **These contracts apply to every run and MUST be followed. They are stated in this always-loaded file — not in steering files — because violating them produces silent data loss and corrupt reports. Every contract is a fix for a specific failure mode observed in production runs.**

### Contract 1: No-Polling Contract (subagents must not panic during long ATX runs)

`atx custom def exec` is long-running: 5–15 minutes for per-repo TDs, 15–30 minutes for portfolio TDs. Subagents have repeatedly broken correctness by becoming impatient mid-run, inspecting filesystem state before ATX has finished writing, then panicking and retrying. The retry corrupts state because two ATX processes against the same repo path produce divergent staging branches.

**The contract:**

1. **Issue exactly one `executeBash` call** for the ATX command, with the configured timeout (1200000 ms per-repo, 1800000 ms portfolio). Do not pre-launch, do not background, do not split.
2. **Do NOT call `ls`, `find`, `cat`, `grep`, or any filesystem inspection tool against the repo's assessment folders while ATX is running.** The agent's executeBash call IS the wait. There is no work to do until it returns.
3. **Do NOT read ATX log files or `~/.aws/atx/custom/...` paths during the run.** ATX writes incrementally; partial reads produce misleading state.
4. **Do NOT spawn a second subagent or a parallel executeBash to "check on" the first one.**
5. **Do NOT interpret stdout buffering pauses, "Thinking..." spinners, or quiet periods as failure.** ATX runs with no stdout output for minutes at a time; this is normal.
6. **Do exactly one filesystem check after executeBash returns** (success, error, or timeout). The `.md` presence is the authoritative success signal — all four artifacts are produced together or none are:
   ```bash
   ls {repo}/agentic-readiness-assessment/{slug}-ara-report.md 2>/dev/null     # ARA
   ls {repo}/modernization-assessment/{slug}-mod-report.md 2>/dev/null         # MOD
   ls {repo}/bpmn-opportunity-assessment/{slug}-bpmn-opportunity-report.md 2>/dev/null  # BAO
   ```
7. If the `.md` file exists → **SUCCESS**, regardless of executeBash exit code or timeout status.
8. If the `.md` file is missing AND executeBash returned a clear error → **FAILURE** with the error.
9. If the `.md` file is missing AND executeBash timed out with no error → **TIMEOUT**. Recommend manual re-run with extended timeout. Do NOT retry inside the subagent.
10. **Never retry a transformation that may still be running.**

**Recovery from panicked subagent:** If you observe a subagent making multiple filesystem inspections during what should be a single ATX wait, the run is compromised. Stop that subagent and re-launch the TD freshly. Do not try to salvage partial state from the panicked run.

### Contract 2: Per-Repo Serialization Rule (`full` mode)

Each ATX execution forks a per-execution staging branch (`atx-result-staging-<timestamp>-<id>`) by stashing+committing local changes onto that branch and then restoring the original branch. **Two ATX executions against the same repo path concurrently each fork their own staging branch from the same starting HEAD**, never see each other's commits, and produce divergent histories.

**The contract:**

- Within a single repository, assessments MUST run sequentially: ARA → MOD → BAO
- Across repositories, run subagents fully in parallel (one subagent per repo)
- **One subagent per repo, never more.** The subagent sequences its assigned TDs.

The serialization adds at most one TD's runtime to each repo (~10–15 minutes) but eliminates the entire class of staging-branch race conditions: lost artifacts, reports written to wrong nested paths (e.g., `monolith/services/monolith/...`), and merge conflicts on regenerated files.

**Per-portfolio branch isolation (recommended):** Before invoking the orchestrator on operator-owned repos, create a dedicated branch (`git checkout -b portfolio-run-<date>`). All ATX staging branches will fork from this branch. At the end you have a single isolated branch you can merge or delete as a unit.

### Contract 3: Portfolio TD Serialization

All portfolio TDs (Portfolio ARA, Portfolio MOD, Portfolio BAO, Bridge) execute against the same workspace root with `-p .`. They share a single git HEAD. Running two portfolio TDs concurrently triggers the same staging-branch divergence that Contract 2 prevents at the repo level.

**The contract:**

- Run portfolio TDs strictly serially in this order: **Portfolio ARA → Portfolio MOD → Portfolio BAO → Bridge**
- A **Reconciliation Gate** runs between each invocation (see `steering/reconciliation-gate.md` for Checks A/B/C)
- Abort the chain if any gate fails — do not proceed to the next portfolio TD with a corrupted workspace

The portfolio phase typically takes ~1 hour for a full assessment with all four portfolio TDs. This is the cost of correctness; do not optimize it away by parallelizing.

**Cross-repo per-repo subagents remain parallel** — only the portfolio aggregation step is serialized.

---

## How Kiro Orchestrates (High-Level)

Detailed step-by-step flow lives in `steering/orchestration-workflow.md`. Summary:

1. **Pre-flight (Step 0):** Verify AWS credentials, ATX CLI, TD existence in registry. Fail fast on any failure.
2. **Parse and validate `portfolio-config.yaml`:** assessment_type, repos, preferences, dependency_overrides, TD names.
3. **Classify each repo:** Apply the decision tree (or honor user-provided `repo_type` override).
4. **Clone missing repos:** For entries with `repository_url` and a non-existent `path`.
5. **Generate ATX configs:** Per-repo ARA (no preferences), per-repo MOD (no agent_scope, merged preferences). Portfolio configs include structured `service_inventory[]` and `dependency_overrides[]`.
6. **Per-repo execution (Contract 2):** One subagent per repo. Subagent runs its assigned TDs sequentially within the repo. All subagents in parallel across repos.
7. **Reconciliation Gate (Step 1.5):** Check A (branch consolidation), Check B (canonical paths — auto-rename and auto-move strays since Contract 2 makes their attribution unambiguous, ABORT only when ≥2 strays exist for the same TD in one repo), Check C (four-artifact bundle completeness, `.json` mandatory). Abort before any portfolio TD if any check fails.
8. **Portfolio TDs (Contract 3):** Strictly serial — Portfolio ARA → Portfolio MOD → Portfolio BAO → Bridge — with a Reconciliation Gate between each.
9. **Consolidate reports:** Copy per-repo reports into top-level `agentic-readiness-assessment/`, `modernization-assessment/`, `bpmn-opportunity-assessment/` folders. Bridge report stays at workspace root. Clean up `.atx-config-*.yaml` and `bpmn-analysis.json`.

> All `atx` commands MUST use `-x` (non-interactive) and `-t` (trust all tools) — assessments run at scale without human intervention. Always pass **absolute paths** to `-p` and `-g`; relative paths silently break across `executeBash` boundaries because each call starts a fresh shell. See `steering/atx-cli-reference.md` for full flag details and `steering/troubleshooting.md` for the path-corruption failure mode.

---

## Quick Start

### 1. Create `portfolio-config.yaml`

Minimum config to validate the toolchain:

```yaml
portfolio_name: "my-platform"
assessment_type: "full"
context: "Building customer-facing AI agents while modernizing legacy services"
agent_scope: "read-only"

transformation_definitions:
  agentic_readiness: "agentic-readiness-assessment"
  modernization: "modernization-assessment"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"
  portfolio_bridge: "portfolio-bridge"

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
agentic-readiness-assessment/
├── service-a-ara-report.{md,json,html,metadata.json}
├── service-b-ara-report.{md,json,html,metadata.json}
└── my-platform-portfolio-ara-report.{md,json,html,metadata.json}

modernization-assessment/
├── service-a-mod-report.{md,json,html,metadata.json}
├── service-b-mod-report.{md,json,html,metadata.json}
└── my-platform-portfolio-mod-report.{md,json,html,metadata.json}

bpmn-opportunity-assessment/                                     ← only when BAO ran
├── process-a-bpmn-opportunity-report.{md,json,html,metadata.json}
└── my-platform-portfolio-bao-report.{md,json,html,metadata.json}

my-platform-bridge-report.{md,json,html,metadata.json}           ← full + portfolio_bridge
```

### Four-Artifact Bundle

Every per-repo and portfolio assessment emits four files. JSON is authoritative on conflict.

| Artifact | Purpose |
|---|---|
| `{name}-report.md` | Richest-prose narrative (rubric quotes, BLOCKER remediation blocks, score tables, top gaps, decomposition strategy, pathway details, execution roadmap, risk register) |
| `{name}-report.json` | **Canonical machine-readable contract.** Consumed by the webapp dashboard and by portfolio TDs. |
| `{name}-report.html` | Single self-contained HTML — no external asset fetches at render time. Every value originates from the JSON. |
| `{name}-report.metadata.json` | Tiny sidecar carrying `{assessment_type, assessment_date, td_version}`. Same fields are also at the root of the main JSON under `metadata`. |

The Reconciliation Gate (Check C) treats `.json` as mandatory — portfolio TDs cannot aggregate without it.

---

## Best Practices

1. **Choose the right `assessment_type`** — ARA for agent safety, MOD for cloud maturity, BAO for BPMN process analysis, `full` for all three with the Bridge cross-cutting view.
2. **Provide `context`** — Free-text portfolio context frames recommendations far better than letting the TD reason from code alone.
3. **Set `agent_scope` for ARA** — `write-enabled` for agents that modify data, `read-only` for observation-only. Affects conditional BLOCKER severity.
4. **Use `preferences` to steer MOD** — Global `prefer`/`avoid` arrays plus per-repo overrides. See `steering/portfolio-config.md` for merge rules.
5. **Specify `repo_type` when obvious** — Skip auto-detection for clearly-infrastructure repos (`infrastructure-only`) or libraries (`library`).
6. **Document dependencies** — Use `dependency_overrides[]` for implicit dependencies the orchestrator cannot infer from code analysis.
7. **Set priorities where helpful** — `P0` for critical services, `P1` for high priority, `P2` for medium. Optional but improves portfolio roadmap sequencing.
8. **Run individual assessments first** — Portfolio assessments require completed individual reports. The reconciliation gate enforces this, but configuring `assessment_type: full` is the simplest path.
9. **Create a portfolio-run branch first** — Prevents ATX staging branches from polluting `main`. Cleanup is one merge instead of many.
10. **Run the Reconciliation Gate manually if running TDs by hand** — Same Checks A/B/C apply. See `steering/reconciliation-gate.md`.
11. **Leverage cross-repo parallelism** — Kiro spawns one subagent per repository so larger portfolios scale near-linearly. Per-repo serialization within `full` mode is mandatory but adds at most one TD's runtime per repo.
12. **Address cross-cutting concerns first** — Portfolio reports surface gaps that affect multiple services. Fix those before per-service work.
13. **Follow dependency order in modernization** — Modernize upstream services before their downstream dependents.
14. **Validate config against the JSON schema** — `ajv validate -s portfolio-config.schema.json -d portfolio-config.yaml` before running.

---

## Troubleshooting

For all error scenarios — missing reports, ATX timeouts, panicked subagents, Bridge failures, configuration errors, branch hygiene issues — read `steering/troubleshooting.md`.

Most common issues:
- **Reports missing → Reconciliation Gate failure.** Reports may be at non-canonical paths or stranded on staging branches.
- **`.json` missing but `.md` exists → mandatory abort.** Re-run that per-repo TD.
- **ATX timeout but report exists → SUCCESS.** No-Polling Contract treats this as success regardless of executeBash exit status.
- **Subagent panic → kill and re-launch.** Don't try to salvage partial state.
- **Parallel `atx custom def publish` fails → publish serially.** The CLI uses a shared tar staging path.

---

## Limitations

- Minimum 2 services for portfolio assessment
- Per-repo assessments must succeed before portfolio aggregation
- Dependency detection is code-analysis-based — declare implicit dependencies via `dependency_overrides[]`
- Preferences are guidance, not guarantees
- Preferences are MOD-only (silently ignored by ARA)
- Assessment quality depends on code completeness and documentation availability

---

## Related Resources

- [AWS Transform Documentation](https://docs.aws.amazon.com/transform/)
- [AWS Transform CLI Reference](https://docs.aws.amazon.com/transform/latest/userguide/custom-command-reference.html)
- [AWS Modernization Pathways](https://skillbuilder.aws/learning-plan)
- [Cloud Design Patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
