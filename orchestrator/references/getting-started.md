# Getting Started

First-time setup for running portfolio analyses with AWS Transform Continuous Modernization. Read this when a user is setting up the orchestrator for the first time, or when prerequisites need to be verified.

---

## Prerequisites

1. **Valid AWS credentials** — The orchestrator checks credentials before doing anything else.
   ```bash
   aws sts get-caller-identity
   ```

2. **AWS Transform CLI** installed and up-to-date
   ```bash
   env -u TOOLBOX_TOOL_VERSION atx --version   # NOT a bare `atx --version` — see below
   # If not installed: https://docs.aws.amazon.com/transform/
   ```
   Inside Claude Code a bare `atx --version` misreports Builder Toolbox's version (`2.1.x`), which
   atx inherits from `$TOOLBOX_TOOL_VERSION`. Unset it to get the real version. Everything in this
   guide is verified against **atx 3.9.0**.

3. **ct healthy** — analyses run in-process, so there is no server to start
   ```bash
   atx ct status --health
   ```

4. **Repository access** — Repositories can be:
   - Already cloned locally (use `--provider local --path <parent-dir>`)
   - In a GitHub/GitLab/Bitbucket org (use the appropriate provider with token)

---

## Pre-flight Sequence

When the user asks to run an analysis, perform these checks in order. Fail fast on any failure.

### Step 0: AWS Credentials

```bash
aws sts get-caller-identity
```

If this fails, terminate immediately with:

```
ERROR: AWS credentials are not valid. Cannot proceed with analysis.
Run 'aws sts get-caller-identity' to diagnose. Common fixes:
- Run 'aws sso login' if using SSO
- Check AWS_PROFILE environment variable
- Verify credentials are not expired
```

**Do NOT proceed to any subsequent step if credentials are invalid.**

### Step 0.1: ATX CLI Available

```bash
env -u TOOLBOX_TOOL_VERSION atx --version
```

If `atx: command not found`, point the user to https://docs.aws.amazon.com/transform/ for installation.

### Step 0.2: Check ct Health

```bash
atx ct status --health
```

This is an in-process check, not a ping against a daemon. There is nothing to start first.

**Never run `atx ct server`.** It still exists but is hidden and deprecated: it starts a real daemon
that blocks the shell until killed, and no `atx ct` command needs it.

### Step 0.3: Verify Source Connectivity

```bash
atx ct source list
```

If no sources are configured, guide the user through `atx ct source add` (see POWER.md "Source Providers").

If a source shows `SETUP_REQUIRED` → credentials are not configured on this machine. Re-add the source.
If a source shows `AUTH_REQUIRED` → token is invalid or expired. Re-add with a fresh token.

---

## First Run Walkthrough (Local Source)

For users running the orchestrator for the first time with local repos:

```bash
# 1. Verify ct is healthy (no server to start)
atx ct status --health

# 2. Add local source pointing to parent directory of repos (use absolute path)
atx ct source add --name my-portfolio --provider local --path "$(pwd)/services"

# 3. Discover repos (scans for .git subdirectories)
atx ct discovery scan --source my-portfolio

# 4. Verify repos were discovered
atx ct repository list

# 5. Run ARA analysis (returns immediately with an analysis ID)
atx ct analysis run --type agentic-readiness --source my-portfolio

# 6. Poll until status is complete (every 30-60s)
atx ct analysis get --id <analysis-id>

# 7. Check findings
atx ct findings list --json

# 8. Locate the reports on disk
atx ct analysis get --id <analysis-id> --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'
```

`analysis run` does accept a hidden `--wait`, but prefer polling in agent workflows — a blocking call
gives the user no progress signal for the 5–15 min per repo an analysis takes.

### Important: `report_paths` Is Not the Whole Bundle

Verified on 3.9.0, `report_paths` listed only the `.md`, while the full 4-artifact bundle
(`.md`, `.json`, `.html`, `.metadata.json`) was written into the repo working tree at
`services/<repo>/{agentic-readiness,modernization-readiness}-analysis/`. The `.json` that downstream
tooling consumes is often only there, so check the working tree too — don't stop at `report_paths`.

### Important: Local Source Path

The `--path` for local sources must be a **parent directory** containing repositories as subdirectories. The scanner looks for child directories with a `.git` folder.

**Always use absolute paths.** Relative paths may not resolve correctly depending on the working directory the CLI was invoked from.

```
✅ --path /home/user/services          (services/repo-a/.git, services/repo-b/.git)
❌ --path ./services                   (relative — may break if the CWD differs later)
❌ --path /home/user/services/repo-a   (this is a repo itself, not a parent of repos)
```

---

## First Run Walkthrough (GitHub Source)

```bash
# 1. Verify ct is healthy (no server to start)
atx ct status --health

# 2. Add GitHub source with PAT (needs 'repo' scope)
atx ct source add --name my-github --provider github --org my-org --token ghp_xxxxxxxxxxxx

# 3. Discover repos
atx ct discovery scan --source my-github

# 4. Verify repos
atx ct repository list

# 5. Run analysis, then poll for completion
atx ct analysis run --type agentic-readiness --source my-github
atx ct analysis get --id <analysis-id>
```

---

## Compute Options

`ct` supports three compute options:

| Option | Description | Best for |
|---|---|---|
| **Local** (default) | Runs on your machine, no extra infra | Trying out, small repos, individual use |
| **Amazon EC2** | Persistent instance in your AWS account | Larger analyses, scheduled recurring runs |
| **AWS Batch (Fargate)** | Serverless containers | Burst workloads, cost-effective at scale |

For EC2 or Batch setup, ask the agent: "Set up an EC2 instance for continuous modernization" or "Set up Batch execution for continuous modernization."

---

## What Runs Where

| Concern | Component | Owns |
|---|---|---|
| Source & findings state | `atx ct` (in-process) | Source management, discovery, analysis scheduling, findings store |
| Analysis execution | ct analysis engine | Per-repo analysis, portfolio aggregation, parallel execution, git state |
| Findings & remediation | ct findings/remediation | Finding storage, severity, status, PR/MR generation |
| Report artifacts | on-disk artifact store + repo working tree | Per-repo and portfolio reports (located via `analysis get --json` → `report_paths`) |
| Execution Plan (EBA) | `atx custom def exec` | Reads report artifacts, generates execution roadmap |

The Power is a thin orchestrator. All analysis logic lives in `ct` itself and the transformation definitions it executes.
