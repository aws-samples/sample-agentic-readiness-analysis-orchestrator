# Execution Plan Generation

How to run the Execution Plan (EBA) TD after ARA and MODA analyses are complete. Read this when the user wants to generate a dependency-aware execution roadmap from analysis findings.

> **The Execution Plan still uses `atx custom def exec`** — it is NOT run via `atx ct analysis run`. This is because the EBA TD requires structured JSON report artifacts as input and produces a roadmap document, not findings.

---

## When to Run

- After **both** ARA and MODA analyses are complete (status: `complete`)
- The user asked for `analysis_type: full` (which includes EBA)
- The user explicitly requests an execution plan / roadmap

---

## Prerequisites

1. **ARA analysis complete**: `atx ct analysis list --type agentic-readiness` shows status `complete`
2. **MODA analysis complete**: `atx ct analysis list --type modernization-readiness` shows status `complete`
3. **Report artifacts available**: `atx ct analysis list-artifacts --id <ara-id>` returns artifacts
4. **No concurrent `atx ct analysis run` in progress** — the ct server and custom exec may conflict on git state

---

## Retrieving Artifacts for EBA Input

Since ct stores artifacts in its internal store (not on disk), you must export them before running EBA:

```bash
# Get the analysis IDs
ara_id=$(atx ct analysis list --type agentic-readiness --status complete --json | jq -r '.[0].id')
moda_id=$(atx ct analysis list --type modernization-readiness --status complete --json | jq -r '.[0].id')

# List available artifacts
atx ct analysis list-artifacts --id $ara_id --json
atx ct analysis list-artifacts --id $moda_id --json

# Export per-repo reports to local files
atx ct analysis get-artifact --id $ara_id --repo <source>::<repo-name> --name report > ./ara-reports/<repo-name>.json
atx ct analysis get-artifact --id $moda_id --repo <source>::<repo-name> --name report > ./moda-reports/<repo-name>.json
```

---

## Configuration File

Create `atx-config-exec-plan.yaml`:

```yaml
additionalPlanContext: |
  context: "<portfolio-level context from user>"
  portfolio_name: "<portfolio-name>"
  service_inventory:
    - name: "service-a"
      path: "./services/service-a"
      priority: "P0"
      repo_type: "application"
      tags: ["monolith", "java"]
    - name: "service-b"
      path: "./services/service-b"
      priority: "P1"
      repo_type: "application"
      tags: ["backend", "python"]
  dependency_overrides:
    - source: "service-a"
      target: "service-b"
      type: "sync"
      description: "REST API calls for inventory checks"
```

### Configuration Fields

| Field | Required | Description |
|---|---|---|
| `context` | Yes | Portfolio-level context describing the overall goal |
| `portfolio_name` | Yes | Name of the portfolio |
| `service_inventory[]` | Yes | Array of services with name, path, priority, repo_type, tags |
| `dependency_overrides[]` | No | Cross-service dependencies for the roadmap |

> **Critical:** `service_inventory[]` and `dependency_overrides[]` MUST be structured YAML object arrays — never free-text bullet lists. The EBA TD parses these programmatically.

---

## Execution Command

```bash
atx custom def exec \
  -n portfolio-execution-plan-generation \
  -p . \
  -g file://atx-config-exec-plan.yaml \
  -x \
  -t
```

### Flags

| Flag | Purpose |
|---|---|
| `-n` | Transformation definition name |
| `-p .` | Workspace root (portfolio-level TD always uses `.`) |
| `-g file://...` | Configuration file with `file://` prefix |
| `-x` | Non-interactive (mandatory for automated runs) |
| `-t` | Trust all tools (mandatory for automated runs) |

### Always Use Absolute Paths in Automated Flows

In subagent/automated flows, compute absolute paths:

```bash
workspace_abs=$(pwd)
config_abs="$workspace_abs/atx-config-exec-plan.yaml"
atx custom def exec \
  -n portfolio-execution-plan-generation \
  -p "$workspace_abs" \
  -g "file://$config_abs" \
  -x -t
```

---

## Timeout

| TD type | timeout (ms) | Wall clock |
|---|---|---|
| Execution Plan | 1800000 | 30 minutes |

Use the `executeBash` tool's `timeout` parameter directly.

---

## Safety Contract

1. **Run ONLY after both ARA and MODA are complete** — verify with `atx ct analysis list`.
2. **Verify report artifacts are available** via `atx ct analysis list-artifacts`.
3. **Issue exactly one `executeBash` call** with timeout 1800000 ms. Do not poll, background, or split.
4. **Do NOT run concurrently with `atx ct analysis run`** — git state conflicts.
5. **After completion**, verify the execution plan artifact exists before reporting success.

---

## Expected Output

The EBA TD produces a **four-artifact bundle** in a `portfolio-execution-plan/` directory at the workspace root:

```
portfolio-execution-plan/
├── {portfolio-name}-portfolio-exec-plan.md           # Narrative roadmap
├── {portfolio-name}-portfolio-exec-plan.json         # Machine-readable plan (canonical)
├── {portfolio-name}-portfolio-exec-plan.html         # Self-contained HTML
└── {portfolio-name}-portfolio-exec-plan.metadata.json # Sidecar metadata
```

The JSON file contains:
- Prioritized execution phases and work streams
- Dependency-aware sequencing across services
- Per-task effort estimates and ownership
- Risk mitigation recommendations
- Decision points for stakeholder review
- Quick wins vs. long-term investments

### Verification

```bash
ls portfolio-execution-plan/*-portfolio-exec-plan.md
```

If the `.md` file exists, the EBA completed successfully.
