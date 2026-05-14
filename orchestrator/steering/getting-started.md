# Getting Started

First-time setup for running portfolio analyses. Read this when a user is setting up the orchestrator for the first time, or when prerequisites need to be verified.

---

## Prerequisites

Kiro orchestrates the analysis workflow, but relies on **AWS Transform CLI** to execute the actual transformations. You need:

1. **Valid AWS credentials** — The orchestrator checks credentials before doing anything else. If credentials are expired or missing, it fails immediately with an actionable error.
   ```bash
   aws sts get-caller-identity
   ```

2. **AWS Transform CLI** installed and configured
   ```bash
   atx --version
   # If not installed: https://docs.aws.amazon.com/transform/
   ```

3. **Transformation definitions** published to your AWS Transform registry. The names are configured in `portfolio-config.yaml`:
   ```yaml
   transformation_definitions:
     agentic_readiness: "your-ara-td-name"
     modernization: "your-mod-td-name"
     portfolio_agentic_readiness: "your-portfolio-ara-td-name"
     portfolio_modernization: "your-portfolio-mod-td-name"
     portfolio_bridge: "your-bridge-td-name"  # optional — only used when analysis_type is "full"
   ```
   Verify they exist:
   ```bash
   atx custom def list | grep your-analysis-name
   ```

4. **Repository access** — Repositories can be:
   - Already cloned locally (just set `path` in the config)
   - Auto-cloned by Kiro (set `repository_url` and `path` — Kiro clones if `path` doesn't exist)

---

## Pre-flight Sequence

When the user asks to run the orchestrator, perform these checks in order. Fail fast on any failure.

### Step 0: AWS Credentials

```bash
aws sts get-caller-identity
```

If this fails, terminate immediately with:

```
ERROR: AWS credentials are not valid. Cannot proceed with analysis.
Run 'aws sts get-caller-identity' to diagnose. Common fixes:
- Run 'ada credentials update' to refresh Midway credentials
- Run 'aws sso login' if using SSO
- Check AWS_PROFILE environment variable
```

**Do NOT proceed to any subsequent step if credentials are invalid.**

### Step 0.1: ATX CLI Available

```bash
atx --version
```

If `atx: command not found`, point the user to https://docs.aws.amazon.com/transform/ for installation.

### Step 0.2: Transformation Definitions Exist

For each TD name configured in `portfolio-config.yaml`'s `transformation_definitions` block:

```bash
atx custom def list | grep <td_name>
```

If any required TD is missing, abort with the specific TD name and instruct the operator to publish it:

```bash
atx custom def publish -n <td_name> --sd ./<td_source_directory> --description "..."
```

> **Parallel publishes will fail** — the atx CLI uses a shared tar staging path (`~/tmp/transformation.tar`). Always publish TDs serially, not in parallel.

### Step 0.3: Repositories Available

For each repo in `repositories[]`:

- If `path` exists locally → skip
- If `path` does not exist AND `repository_url` is set → clone it: `git clone <repository_url> <path>`
- If `path` does not exist AND no `repository_url` → abort with: `Repository {name} has no repository_url and {path} does not exist locally.`

---

## First Run Walkthrough

For users running the orchestrator for the first time, recommend this minimal config to validate the toolchain end-to-end:

```yaml
portfolio_name: "smoke-test"
analysis_type: "agentic-readiness"  # Single TD path = simplest

transformation_definitions:
  agentic_readiness: "agentic-readiness-analysis"
  modernization: "modernization-analysis"
  portfolio_agentic_readiness: "portfolio-agentic-readiness"
  portfolio_modernization: "portfolio-modernization"

repositories:
  - name: "service-a"
    path: "./services/service-a"
  - name: "service-b"
    path: "./services/service-b"
```

Two repos is the minimum for a portfolio analysis. Single-repo analyses should run a per-repo TD directly via `atx custom def exec` (see `manual-execution.md`).

---

## What Runs Where

| Concern | Component | Owns |
|---|---|---|
| Workflow orchestration | This power | Subagent spawning, sequencing, reconciliation |
| Per-repo evaluation | ARA / MOD / BAO TDs (in AWS Transform registry) | Question scoring, finding generation, report rendering |
| Portfolio aggregation | Portfolio ARA / MOD / BAO TDs | Cross-cutting analysis, dependency-aware roadmap |
| Cross-analysis view | Bridge TD | Unified remediation mapping |

The Power is a thin orchestrator. All evaluation logic lives in the TDs, which are versioned independently in your AWS Transform registry.
