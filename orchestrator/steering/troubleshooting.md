# Troubleshooting

Common errors and their resolutions when running the orchestrator. Read this when something fails or produces unexpected results.

---

## Server Issues

### Connection refused or server not running

**Symptom:** Any `atx ct` command returns "Connection refused" or "server not running."

**Fix:**
```bash
atx ct server &
# Wait 3-5 seconds
atx ct status --health
```

If health check still fails:
- Check if port 8081 is already in use: `lsof -i :8081`
- Kill any stale server process and restart
- Check server logs for startup errors

---

## Source Issues

### Discovery scan returns zero repositories

**Symptom:** `atx ct repository list` is empty after discovery scan.

**Fix:** For local sources, verify that `--path` points to a **parent directory** containing repos as subdirectories, NOT to a repo directly.

```bash
# ❌ Wrong — pointing to a repo
atx ct source add --name x --provider local --path ./services/my-app

# ✅ Correct — pointing to parent of repos
atx ct source add --name x --provider local --path ./services
```

The scanner looks for child directories containing a `.git` folder.

### SETUP_REQUIRED error

**Symptom:** Source shows SETUP_REQUIRED status.

**Fix:** The source exists in your account but credentials are not configured locally. Re-add:
```bash
atx ct source remove --name <name>
atx ct source add --name <name> --provider <provider> --path <path>  # or --org for remote
```

### AUTH_REQUIRED error

**Symptom:** Source shows AUTH_REQUIRED.

**Fix:** Token is invalid, expired, or missing required scopes.
- GitHub: needs `repo` scope (classic PAT)
- GitLab: needs `api` scope
- Bitbucket: needs read access for discovery, write for remediation

Re-add with a fresh token.

### Cannot remove source (has repositories)

**Symptom:** `atx ct source remove` returns 409 conflict.

**Fix:** Delete all repos under the source first:
```bash
atx ct repository list --source <name> --json
atx ct repository delete --repo <slug> --source <name>
# Repeat for each repo, then:
atx ct source remove --name <name>
```

---

## Analysis Issues

### INVALID_INPUT error

**Symptom:** `atx ct analysis run` returns INVALID_INPUT.

**Fix:** Verify you are using a valid analysis type name:
- `tech-debt-quick`
- `tech-debt-comprehensive`
- `security`
- `agentic-readiness`
- `modernization-readiness`
- `custom` (requires `--transformation-name`)

### Analysis stuck in "running" state

**Fix:**
1. Check: `atx ct analysis get --id <id>` for per-repo status
2. If stuck > 40 minutes, cancel: `atx ct analysis cancel --id <id>`
3. Re-run: `atx ct analysis run --type <type> --source <name> --wait`

### Analysis completes but no findings

**Possible causes:**
- Repos are already fully compliant
- Analysis type doesn't apply (e.g., security requires security agent setup)
- Repos were not properly discovered (check `atx ct repository list`)

### Configuration flag not accepted

**Symptom:** `atx ct analysis run --type agentic-readiness -g <config>` fails with "unknown option" or similar.

**Cause:** The `-g`/`--configuration` flag is **ONLY valid with `--type custom`**. Built-in analysis types do not accept custom configuration.

**Fix:** Remove the `-g` flag. Built-in types use their own defaults and cannot be customized via configuration files.

### Portfolio aggregation says "fewer than 2 valid reports"

**Symptom:** Portfolio artifact exists but shows analysis failed due to insufficient reports.

**Cause:** The portfolio aggregation requires at least 2 per-repo reports. If you ran analysis on only 1 repo, portfolio aggregation cannot proceed.

**Fix:** Run analysis on at least 2 repos in the same source:
```bash
atx ct analysis run --type agentic-readiness --source my-portfolio --wait
```
Without `--repo`, ct runs analysis on ALL discovered repos.

---

## Artifact Issues

### Report artifacts not found on local filesystem

**Symptom:** After analysis completes, `find . -name "*report*"` returns nothing.

**Cause:** The ct server stores artifacts in its internal artifact store, NOT on the local filesystem. This is by design.

**Fix:** Access artifacts via the API:
```bash
# List available artifacts
atx ct analysis list-artifacts --id <analysis-id> --json

# Get specific artifact content
atx ct analysis get-artifact --id <analysis-id> --repo <repo-slug> --name ara
```

### Unknown artifact name

**Symptom:** `get-artifact` returns "artifact not found."

**Fix:** First list available artifacts to see valid names:
```bash
atx ct analysis list-artifacts --id <analysis-id> --json
```

Artifact names by type:
- ARA per-repo: `ara`
- MODA per-repo: `mod`
- Portfolio ARA: repo=`_portfolio_ara`, name=`report`
- Portfolio MODA: repo=`_portfolio_mod`, name=`report`

---

## Execution Plan (EBA) Issues

### EBA fails with "No such file"

**Symptom:** `atx custom def exec` returns ENOENT.

**Fix:** Usually a path issue:
- Verify `-p` is an absolute path or valid relative path from CWD
- Verify `-g file://...` uses the correct absolute path to the config
- Check CWD hasn't drifted: use absolute paths always in automated flows

### EBA fails with missing report artifacts

**Symptom:** EBA TD starts but can't find input JSON reports.

**Fix:**
1. Verify ARA + MODA analyses are truly `complete` (not just `running`): `atx ct analysis list`
2. Export artifacts from the ct server to local files:
   ```bash
   atx ct analysis get-artifact --id <ara-id> --repo <slug> --name ara > ./ara-reports/<slug>.md
   ```
3. Ensure `service_inventory[].path` in the config matches actual repo paths

### EBA hangs (no output after 30+ minutes)

**Fix:**
- The default timeout is 1800000 ms (30 min). For very large portfolios, increase to 2400000 ms
- If it exceeds timeout, check for credential expiration mid-run: `aws sts get-caller-identity`

### EBA leaves you on a staging branch

**Symptom:** After EBA completes, `git branch --show-current` shows `atx-result-staging-*`.

**Cause:** ATX creates a staging branch for its git operations. This is normal.

**Fix:** Switch back to your working branch:
```bash
git checkout <your-branch>
```
The EBA output (`portfolio-execution-plan/`) will be on the staging branch. Merge or cherry-pick if needed:
```bash
git merge --no-ff atx-result-staging-<timestamp>
```

---

## Credential Issues

### "The security token included in the request is invalid"

**Symptom:** Server log or command output shows security token error.

**Fix:**
```bash
aws sts get-caller-identity
# If expired:
aws sso login
# Then restart the server:
# Kill existing: kill $(lsof -t -i :8081)
atx ct server &
```

### Region not supported

**Symptom:** `AWS Transform is not available in region 'us-west-2'`

**Fix:** Set the region to a supported one:
```bash
export AWS_REGION=us-east-1
```
Note: `atx ct` commands use the region from your AWS config. `atx custom def exec` may require explicit region setting.

---

## Remediation Issues

### Permission errors during remediation

**Symptom:** Remediation fails with permission/auth errors.

**Fix:** Remediation creates branches and PRs/MRs — requires write access:
- GitHub: ensure `repo` scope (full)
- GitLab: ensure `api` scope
- Bitbucket: ensure `write:repository:bitbucket` and `write:pullrequest:bitbucket`

Update token:
```bash
atx ct source remove --name <name>
atx ct source add --name <name> --provider <provider> --org <org> --token <new-token>
```

### Remediation creates branch but no PR

**Symptom:** For local sources, remediation creates a branch but no PR.

**Expected behavior:** Local sources don't have a remote to push PRs to. The remediation creates a local branch with the fix. You can review and merge it manually:
```bash
git -C <repo-path> branch --list 'remediation-*'
git -C <repo-path> merge <branch-name>
```

---

## General Debugging

### Check overall system status

```bash
atx ct status
```

Shows counts for sources, repos, analyses, findings, and remediations.

### Server logs

Server logs go to stdout/stderr. If you started with `atx ct server &`, redirect:
```bash
atx ct server > /tmp/atx-ct-server.log 2>&1 &
```

Then inspect: `tail -f /tmp/atx-ct-server.log`
