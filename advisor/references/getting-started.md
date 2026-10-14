# Getting Started

First-time setup for running the readiness analyses with AWS Transform Continuous Modernization. Read this when a user is setting up for the first time, or when prerequisites need verifying.

---

## Prerequisites

1. **Valid AWS credentials.** Check before doing anything else.

   ```bash
   aws sts get-caller-identity
   ```

2. **The AWS Transform CLI**, installed and current. Baseline for everything in this skill is **`atx` 3.18.0**.

   ```bash
   readlink -f "$(command -v atx)"      # the real version — the install path ends in it
   curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash   # install or upgrade
   ```

   ⚠️ `atx --version` reports an internal build string that does not match the install-path version. **Cite the install path.** And **there is no `atx update` subcommand** — the top-level commands are `custom`, `json`, `mcp` and `ct`. Re-run the installer to upgrade; upgrading in place preserves registered sources, repositories, analyses and findings.

3. **`ct` healthy.** Analyses run in-process, so there is no server to start.

   ```bash
   atx ct status --health
   ```

4. **Repository access.** Either already cloned locally (`--provider local --path <parent-dir>`) or in a GitHub / GitLab / Bitbucket organization (the matching provider plus a token).

5. **For anything past the two managed analyses: the definitions repository cloned, and the custom definitions published into the account you are working in.** ARA and MOD need neither — they are built into `atx ct`. The dependency-graph, bridge, BPMN and execution-plan stages need definitions that resolve by name only once published, and `publish` reads them from a local directory.

   ```bash
   git clone https://github.com/aws-samples/sample-agentic-readiness-analysis-orchestrator.git
   cd sample-agentic-readiness-analysis-orchestrator
   ls definitions/custom/     # six definitions: IAD, bridge, EBA, BAO, portfolio BAO, containerize-service
   ```

   Then publish the ones you need — one `atx custom def publish` per definition, per account. Full recipe, including the `--category` tag that `atx ct` enforces and the one definition that needs a staged copy, is in [`td-catalog.md` §0](td-catalog.md#0-what-you-need-on-disk).

---

## Pre-flight sequence

Run these in order when the user asks for an analysis. Fail fast on any failure.

### Step 0 — AWS credentials

```bash
aws sts get-caller-identity
```

If this fails, terminate immediately:

```
ERROR: AWS credentials are not valid. Cannot proceed with analysis.
Run 'aws sts get-caller-identity' to diagnose. Common fixes:
- Run 'aws sso login' if using SSO
- Check the AWS_PROFILE environment variable
- Verify credentials are not expired
```

**Do NOT proceed to any subsequent step if credentials are invalid.**

### Step 0.1 — CLI available

```bash
command -v atx && readlink -f "$(command -v atx)"
```

If `atx` is not found, point the user at the installer above or https://docs.aws.amazon.com/transform/.

### Step 0.2 — Region

```bash
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1
```

**Only `us-east-1` resolves.** A stray Region elsewhere in the environment makes the endpoint fail to resolve at all, which surfaces as a DNS error rather than a clean "not available" message.

### Step 0.3 — `ct` health

```bash
atx ct status --health
```

An in-process check, not a ping against a daemon — there is nothing to start first. **Never run `atx ct server`**: it is deprecated, starts a real daemon that blocks the shell until killed, and no `atx ct` command needs it.

### Step 0.4 — Source connectivity

```bash
atx ct source list
```

With no sources configured, walk the user through `atx ct source add` (see [`ct-operations.md`](ct-operations.md)). A source showing `SETUP_REQUIRED` means credentials are not configured on this machine — re-add it. `AUTH_REQUIRED` means the token is invalid or expired — re-add with a fresh token.

---

## First run — local source

```bash
# 1. Health check (no server to start)
atx ct status --health

# 2. Add a local source pointing at the PARENT directory of the repos (absolute path)
atx ct source add --name my-portfolio --provider local --path /absolute/path/to/services

# 3. Discover repos (scans for .git subdirectories)
atx ct discovery scan --source my-portfolio

# 4. Verify what was discovered
atx ct repository list

# 5. Run the first analysis (returns immediately with an analysis id)
atx ct analysis run --type modernization-readiness --source my-portfolio

# 6. Poll every 30-60s. `status: complete` fires when the per-repo phase ends while the
#    portfolio phase is still running — a run is genuinely done only once report_paths is
#    non-empty, or the launching process exits.
atx ct analysis get --id <analysis-id> --json \
  | jq -r '"\(.status) report_paths=\(.report_paths // {} | length)"'

# 7. Then the second axis — never concurrently with step 5
atx ct analysis run --type agentic-readiness --source my-portfolio

# 8. Findings and report locations
atx ct findings count --by severity --json
atx ct analysis get --id <analysis-id> --json | jq -r '.report_paths | to_entries[] | "\(.key)\t\(.value.ara // .value.mod)"'
```

`analysis run` accepts `--wait`, but prefer polling in agent workflows — a blocking call gives the user no progress signal for the 5–15 minutes per repository an analysis takes.

### The local source path must be a parent directory

The scanner looks for child directories containing a `.git` folder. **Always use absolute paths**; relative paths may not resolve depending on the working directory the CLI was invoked from.

```
✅ --path /home/user/services          (services/repo-a/.git, services/repo-b/.git)
❌ --path ./services                   (relative — may break if the CWD differs later)
❌ --path /home/user/services/repo-a   (this is a repository, not a parent of repositories)
```

### `report_paths` is markdown-only

`report_paths` lists only the `.md`. The full four-artifact bundle (`.md`, `.json`, `.html`, `.metadata.json`) lives in the source-scoped run tree, which `report_paths` never mentions:

```bash
# everything one run produced
find ~/.atxct/sources -path "*runs/<analysis-id>/*" -type f
# the portfolio bundle — its .html and .json exist here and NOWHERE else
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

**Glob rather than construct these paths.** The segment after `<src>` is the **source's** analysis root, not the run's type (a modernization run can land under `.../agentic-readiness/runs/<id>/`), and per-repo directories are slug-mangled `<source>-<repo>-<16hex>`.

For **local** sources the per-repo bundle is also copied into the working tree at `services/<repo>/{agentic-readiness,modernization-readiness}-analysis/` — per-repo only, never portfolio output. Full detail in [`ct-operations.md`](ct-operations.md).

---

## First run — GitHub source

```bash
atx ct status --health
atx ct source add --name my-github --provider github --org my-org --token <classic-pat>   # 'repo' scope
atx ct discovery scan --source my-github
atx ct repository list
atx ct analysis run --type modernization-readiness --source my-github
atx ct analysis get --id <analysis-id> --json | jq -r '"\(.status) report_paths=\(.report_paths // {} | length)"'
```

For remote sources nothing is committed or pushed to the repositories — `ct` touches repository git only during a remediation.

---

## Compute options

| Option | Infrastructure | Best for |
|---|---|---|
| **Local** (default) | your machine, no extra infrastructure | trying it out, small repositories, individual use |
| **AWS Transform-managed** | none required | the simplest path to off-laptop execution |
| **AWS Batch on Fargate** | a CloudFormation stack in your account | burst workloads, cost-effective at scale (recommended) |
| **Amazon EC2** | a CloudFormation stack in your account | larger analyses, scheduled recurring runs |

All analysis and remediation run **in your AWS account using your credentials**, and your source code stays under your control. Setup commands are in [`ct-operations.md`](ct-operations.md).

---

## Before you run anything — frame it

Running the analysis is the cheap part. Before you spend the wall clock, settle the three framing questions in the main skill's Stage 0: what the estate is by *kind*, whether the customer has declared refactor or reimagine, and who reads the deliverable. Then confirm the estate actually belongs on Continuous modernization at all — see [`transform-paths.md`](transform-paths.md). An estate of VMs in a datacenter is not a Continuous modernization engagement.
