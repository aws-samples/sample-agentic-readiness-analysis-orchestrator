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
   atx --version
   # If not installed: https://docs.aws.amazon.com/transform/
   ```

3. **ct server running** — Required for all `atx ct` commands
   ```bash
   atx ct server &
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
atx --version
```

If `atx: command not found`, point the user to https://docs.aws.amazon.com/transform/ for installation.

### Step 0.2: Start ct Server

```bash
atx ct server &
```

Wait a few seconds, then verify:

```bash
atx ct status --health
```

If you get "Connection refused" → server didn't start. Check for port conflicts or re-run.

The server listens on `http://localhost:8081` by default. Use `--port <port>` for a custom port.

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
# 1. Start the server
atx ct server &

# 2. Add local source pointing to parent directory of repos (use absolute path)
atx ct source add --name my-portfolio --provider local --path "$(pwd)/services"

# 3. Discover repos (scans for .git subdirectories)
atx ct discovery scan --source my-portfolio

# 4. Verify repos were discovered
atx ct repository list

# 5. Run ARA analysis
atx ct analysis run --type agentic-readiness --source my-portfolio --wait

# 6. Check findings
atx ct findings list --json
```

### Important: Local Source Path

The `--path` for local sources must be a **parent directory** containing repositories as subdirectories. The scanner looks for child directories with a `.git` folder.

**Always use absolute paths.** Relative paths may not resolve correctly depending on the server's working directory.

```
✅ --path /home/user/services          (services/repo-a/.git, services/repo-b/.git)
❌ --path ./services                   (relative — may break if server CWD differs)
❌ --path /home/user/services/repo-a   (this is a repo itself, not a parent of repos)
```

---

## First Run Walkthrough (GitHub Source)

```bash
# 1. Start the server
atx ct server &

# 2. Add GitHub source with PAT (needs 'repo' scope)
atx ct source add --name my-github --provider github --org my-org --token ghp_xxxxxxxxxxxx

# 3. Discover repos
atx ct discovery scan --source my-github

# 4. Verify repos
atx ct repository list

# 5. Run analysis
atx ct analysis run --type agentic-readiness --source my-github --wait
```

---

## Compute Options

The ct server supports three compute options:

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
| Server lifecycle | `atx ct server` | Source management, discovery, analysis scheduling, findings store |
| Analysis execution | ct analysis engine | Per-repo analysis, portfolio aggregation, parallel execution, git state |
| Findings & remediation | ct findings/remediation | Finding storage, severity, status, PR/MR generation |
| Report artifacts | ct artifact store | Per-repo and portfolio reports (accessed via `list-artifacts` / `get-artifact`) |
| Execution Plan (EBA) | `atx custom def exec` | Reads report artifacts, generates execution roadmap |

The Power is a thin orchestrator. All analysis logic lives in the ct server and the transformation definitions it executes.
