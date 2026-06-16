# Execution Plan Generation

How to generate a portfolio-level unified execution plan from completed MODA and/or ARA reports. Read this when the user wants to produce an execution plan, or when `analysis_type` includes execution planning.

> **DEPENDENCY (at least one required):** The execution plan TD consumes the portfolio MODA report AND/OR the portfolio ARA report as its analytical inputs. At least one must exist. When both exist, the TD produces a unified plan covering modernization work streams (from MODA) and agent-readiness work streams (from ARA) with cross-dimension dependency detection.
>
> ```
> Per-service MODA (×N, parallel) → Portfolio MODA ─┐
>                                                    ├→ Portfolio Execution Plan
> Per-service ARA (×N, parallel) → Portfolio ARA ───┘
> ```
>
> If neither report exists, the execution plan TD will terminate with an error. At least one pipeline must complete first.

---

## When to Use

- After a MOD, ARA, or `full` analysis has completed **and** at least one portfolio-level report exists
- The user wants an execution roadmap with phased timelines, cost estimates, and risk analysis
- The user needs work stream decomposition for cross-team planning (modernization AND/OR agent-readiness)
- The user wants decision points and success metrics for an engagement
- The user wants a unified view of both modernization and agent-readiness work

**When NOT to use:**
- Neither portfolio MODA report nor portfolio ARA report exists — run analysis first
- Individual per-service reports exist but no portfolio aggregation has run

---

## Gathering Engagement Parameters

Before generating the ATX configuration, ask the user for the following engagement parameters. Each is optional — defaults are applied if omitted.

| Parameter | Question to ask | Default |
|---|---|---|
| `team_size` | How many engineers are available for modernization work? | 5 |
| `timeline_constraint` | Is there a hard deadline or desired completion window? (e.g., "6 months", "Q4 2026") | unconstrained |
| `budget_constraint` | What is the budget envelope? (e.g., "$500K total", "minimize cost", "no constraint") | — |
| `compliance_requirements` | Are there regulatory frameworks that must be maintained during migration? (e.g., PCI-DSS, SOC2, HIPAA) | — |
| `availability_requirement` | What uptime SLA must be maintained during migration? (e.g., "99.9%", "zero-downtime") | — |
| `risk_tolerance` | What is the team's risk tolerance? (`conservative`, `moderate`, `aggressive`) | moderate |
| `existing_capabilities` | What does the team already have? (e.g., "Strong K8s, Terraform, CI/CD") | — |
| `preferences` | Technology preferences — what to prefer and what to avoid? | from portfolio-config.yaml |
| `priority_pathways` | Should we plan for all triggered pathways, or only a subset? | all triggered |

**Workflow:**

1. Present these parameters to the user in a structured list
2. Accept answers (partial answers are fine — defaults fill gaps)
3. Build the ATX configuration file from the answers
4. Execute the TD

---

## Building the ATX Configuration

Generate `atx-config-exec-plan.yaml` with the user's answers merged into `additionalPlanContext`:

```yaml
additionalPlanContext: |
  portfolio_name: "{from portfolio-config.yaml}"
  team_size: {user answer or 5}
  timeline_constraint: "{user answer}"
  budget_constraint: "{user answer}"
  compliance_requirements: [{user answers as array}]
  availability_requirement: "{user answer}"
  risk_tolerance: "{user answer or moderate}"
  existing_capabilities: "{user answer}"
  preferences:
    prefer: [{merged from portfolio-config.yaml + user overrides}]
    avoid: [{merged from portfolio-config.yaml + user overrides}]
```

**Generation rules:**

1. `portfolio_name` — from `portfolio-config.yaml` (same value used for MODA runs)
2. `team_size` — user answer, default 5
3. `timeline_constraint` — user answer, omit if not provided
4. `budget_constraint` — user answer, omit if not provided
5. `compliance_requirements` — user answer as YAML array, omit if empty
6. `availability_requirement` — user answer, omit if not provided
7. `risk_tolerance` — user answer, default "moderate". Must be one of: `conservative`, `moderate`, `aggressive`
8. `existing_capabilities` — user answer as free-text string, omit if not provided
9. `preferences` — merge: start with global `preferences` from `portfolio-config.yaml`, then override with any user-provided preferences. Same merge rules as MOD configs (see `steering/portfolio-config.md`).
10. `priority_pathways` — user answer as YAML array, omit if user wants all triggered pathways planned

**Omit fields entirely if the user did not provide a value and there is no default.** Do not emit empty strings or empty arrays for omitted fields.

---

## Execution

### Prerequisites (Mandatory — Fail Fast)

The execution plan TD requires at least one portfolio-level report. **Check for existence before proceeding.**

```
Dependency chain (at least one path required):
  Path A: Per-service MOD (×N) → Portfolio MODA → ┐
                                                   ├→ Portfolio Execution Plan TD
  Path B: Per-service ARA (×N) → Portfolio ARA → ─┘
```

Before running the execution plan TD:

1. **At least one portfolio report MUST exist:**
   - Portfolio MODA report at `./portfolio-modernization-readiness-analysis/{portfolio-name}-mod-portfolio-report.json` — AND/OR —
   - Portfolio ARA report at `./portfolio-agentic-readiness-analysis/{portfolio-name}-ara-portfolio-report.json`
2. **Verify presence — abort if NEITHER exists:**
   ```bash
   MODA=$(ls ./portfolio-modernization-readiness-analysis/*-mod-portfolio-report.json 2>/dev/null)
   ARA=$(ls ./portfolio-agentic-readiness-analysis/*-ara-portfolio-report.json 2>/dev/null)
   if [ -z "$MODA" ] && [ -z "$ARA" ]; then
     echo "ERROR: Neither portfolio MODA report nor portfolio ARA report found."
     echo "The execution plan TD requires at least one. Run 'modernization', 'agentic-readiness', or 'full' analysis first."
     exit 1
   fi
   echo "Found: MODA=${MODA:-none} ARA=${ARA:-none}"
   ```
   **Do NOT proceed if both are missing.**
3. **Validate report(s)** contain at least 2 assessed services:
   ```bash
   grep -o '"services_assessed":[0-9]*' ./portfolio-modernization-readiness-analysis/*-mod-portfolio-report.json 2>/dev/null
   grep -o '"services_assessed":[0-9]*' ./portfolio-agentic-readiness-analysis/*-ara-portfolio-report.json 2>/dev/null
   ```

### TD Name

The execution plan TD is registered as:

```
portfolio-execution-plan-generation
```

Verify it exists in the registry:

```bash
atx custom def list | grep portfolio-execution-plan-generation
```

If missing, publish it from the definitions directory:

```bash
atx custom def publish \
  -n portfolio-execution-plan-generation \
  --sd ./definitions/portfolio-execution-plan-generation \
  --description "Generate portfolio-level unified execution plan from aggregated MODA and/or ARA reports"
```

### Invocation

```bash
atx custom def exec \
  -n portfolio-execution-plan-generation \
  -p . \
  -g file://atx-config-exec-plan.yaml \
  -x \
  -t
```

Always use:
- `-p .` — the TD operates at the portfolio root (reads from `./portfolio-modernization-readiness-analysis/`)
- `-x` — non-interactive
- `-t` — trust all tools
- Absolute paths for `-p` and `-g` in subagent flows (see `steering/atx-cli-reference.md`)

**Timeout:** 1800000 ms (30 minutes). The execution plan TD reads reports and generates complex planning artifacts — allow the same timeout as portfolio TDs.

### Verification

After `atx custom def exec` returns, verify the output exists:

```bash
ls ./portfolio-execution-plan/{portfolio-name}-portfolio-exec-plan.md 2>/dev/null
```

**Success signal:** presence of the `.md` file. All four artifacts are produced together or none are:
- `{portfolio-name}-portfolio-exec-plan.md`
- `{portfolio-name}-portfolio-exec-plan.json`
- `{portfolio-name}-portfolio-exec-plan.html`
- `{portfolio-name}-portfolio-exec-plan.metadata.json`

---

## Output

The execution plan TD produces a four-artifact bundle in `./portfolio-execution-plan/`:

| Artifact | Purpose |
|---|---|
| `{name}-portfolio-exec-plan.md` | Narrative execution plan — work streams, timeline, risk register, cost estimates |
| `{name}-portfolio-exec-plan.json` | Canonical machine-readable contract |
| `{name}-portfolio-exec-plan.html` | Self-contained HTML visualization with timeline and risk views |
| `{name}-portfolio-exec-plan.metadata.json` | Version sidecar |

---

## Relationship to Other Steering Files

| Steering file | Relationship |
|---|---|
| `orchestration-workflow.md` | The orchestrator can chain execution plan generation after portfolio MOD and/or ARA completes |
| `portfolio-config.md` | `portfolio_name` and `preferences` are sourced from the same config |
| `manual-execution.md` | Execution plan can be run manually without the orchestrator |
| `reconciliation-gate.md` | The reconciliation gate does NOT gate the execution plan TD — it gates portfolio ARA/MOD TDs only. The exec plan TD depends solely on at least one portfolio report existing. |

---

## Common Scenarios

### Full pipeline (orchestrator-driven)

When `analysis_type: full` completes, the orchestrator can prompt the user: "Both MODA and ARA reports are ready. Would you like to generate a unified execution plan?" If yes, gather engagement parameters and run the execution plan TD. The TD will automatically consume both reports and produce a unified plan with cross-dimension dependencies.

### MODA-only pipeline

When only `analysis_type: modernization` has been run, the execution plan TD produces modernization work streams only. ARA sections are omitted.

### ARA-only pipeline

When only `analysis_type: agentic-readiness` has been run, the execution plan TD produces agent-readiness work streams only. Modernization sections are omitted.

### Standalone execution (manual)

```bash
# 1. Verify at least one portfolio report exists
ls ./portfolio-modernization-readiness-analysis/*-mod-portfolio-report.json 2>/dev/null
ls ./portfolio-agentic-readiness-analysis/*-ara-portfolio-report.json 2>/dev/null

# 2. Create atx-config-exec-plan.yaml with engagement parameters

# 3. Run the TD
atx custom def exec -n portfolio-execution-plan-generation -p . -g file://atx-config-exec-plan.yaml -x -t

# 4. Verify output
ls ./portfolio-execution-plan/*-portfolio-exec-plan.md
```

### Re-running with different parameters

The execution plan TD is safe to re-run — it reads reports but does not modify them. To generate an alternative plan (e.g., different risk tolerance or team size), update `atx-config-exec-plan.yaml` and re-run. Previous output is overwritten.
