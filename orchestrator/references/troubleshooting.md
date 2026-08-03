# Troubleshooting

Common errors and their resolutions when running the orchestrator. Read this when something fails or produces unexpected results.

---

## Connectivity Issues

### Never start a server — there isn't one to start

**Symptom:** A command failed and you're tempted to run `atx ct server` (an older note or doc may have told you to).

**Cause (verified 2026-08, atx 3.9.0):** No server is needed. `atx ct` analyses run **in-process** — the CLI does the work itself. `atx ct server` is a hidden/deprecated command that starts a daemon and **blocks the shell** until killed; in an automated flow it will hang the session outright.

**Fix:** Never invoke `atx ct server`. Health-check with:
```bash
atx ct status --health
```

If the health check fails, the cause is credentials or region (see "Credential Issues") — **"server not running" is never a valid diagnosis** for any `atx ct` failure.

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
3. Re-run: `atx ct analysis run --type <type> --source <name>`

Note on `--wait`: it **does** exist on `analysis run` — it's just hidden from `--help` (registered with `.hideHelp()`), so its absence from the help text is not evidence it was removed. In agent workflows prefer explicit polling of `atx ct analysis get --id <id> --json` over `--wait`, so you keep control of the timeout and can report progress.

### Analysis completes but reports 0 findings

**Symptom:** Analysis reaches `complete`, report artifacts are written, but the findings count is 0.

**Cause (atx 3.7.0 bug):** the report parser fell back to markdown scraping whenever `categories` was emitted as a JSON array, and silently extracted nothing. **Fixed in 3.9.0** — verified 43 findings on an ARA and 31 on a MOD run.

**Fix:** upgrade the CLI. There is **no `atx update` subcommand** — re-run the installer:
```bash
curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash
```
Upgrading in place preserves your registered sources, repos, and prior analyses — you do not need to re-register or re-run anything.

Verify the version (see "`atx --version` misreports inside Claude Code" below):
```bash
env -u TOOLBOX_TOOL_VERSION atx --version
```

If you are already on 3.9.0+, then consider the benign causes:
- Repos are already fully compliant
- Analysis type doesn't apply (e.g., security requires security agent setup)
- Repos were not properly discovered (check `atx ct repository list`)

### Configuration flag not accepted

**Symptom:** `atx ct analysis run --type agentic-readiness -g <config>` fails with "unknown option" or similar.

**Cause:** The `-g`/`--configuration` flag is **ONLY valid with `--type custom`**. Built-in analysis types do not accept custom configuration.

**Fix:** Remove the `-g` flag. Built-in types use their own defaults and cannot be customized via configuration files.

### `schedule create --expression` is rejected

**Symptom:** `atx ct schedule create --expression "<cron>"` fails on the unknown option.

**Cause:** `--expression` (and cron syntax generally) was **removed in 3.8.0**. Schedules now take a fixed set of recurrence keywords.

**Fix:** Use `--recurrence`, which is now required:
```bash
atx ct schedule create --type agentic-readiness --source <name> --recurrence daily
# also: --recurrence weekly:MONDAY   |   --recurrence monthly:1
```

### Portfolio aggregation says "fewer than 2 valid reports"

**Symptom:** Portfolio artifact exists but shows analysis failed due to insufficient reports.

**Cause:** The portfolio aggregation requires at least 2 per-repo reports. If you ran analysis on only 1 repo, portfolio aggregation cannot proceed.

**Fix:** Run analysis on at least 2 repos in the same source:
```bash
atx ct analysis run --type agentic-readiness --source my-portfolio
```
Without `--repo`, ct runs analysis on ALL discovered repos.

### "no portfolio ARA report found" / "no portfolio MOD report found"

**Symptom:** A portfolio TD phase errors out saying it found no portfolio report to work from.

**Cause (verified 2026-08, atx 3.9.0):** This is **not a bug** if you ran against a single repo. Both portfolio TDs require **>= 2 discovered per-repo reports** to aggregate, and aggregation is **per-run** — a run only sees the reports produced within itself. Two separate single-repo runs do **not** accumulate into a 2-report portfolio.

Additionally, the `bridge_summary` phase needs **both** a portfolio ARA report **and** a portfolio MOD report present. Having only one of the two is enough to fail it, even with 2+ repos.

**Fix:** Run one analysis over a source with 2+ discovered repos (omit `--repo`), and run **both** ARA and MOD before expecting `bridge_summary` to succeed.

---

## Artifact Issues

### Where the report artifacts actually are

**Symptom:** After analysis completes you don't know where to look, or `find . -name "*report*"` from the wrong directory returns nothing.

**Cause (verified 2026-08, atx 3.9.0):** Reports **ARE** on the local filesystem. They are written to **two** places, and you generally want to check both:

1. The shared analysis store, keyed by analysis id:
   ```
   ~/.atxct/shared/analyses/<analysis-id>/artifacts/<source>__<repo>/
   ```
2. For **local** sources, directly into the repo working tree:
   ```
   services/<repo>/agentic-readiness-analysis/<repo>-ara-report.{md,json,html,metadata.json}
   services/<repo>/modernization-readiness-analysis/<repo>-mod-report.{md,json,html,metadata.json}
   ```

Portfolio output lands under the run directory:
```
<run>/portfolio-<name>/agentic-readiness-analysis/
<run>/portfolio-<name>/modernization-readiness-analysis/
```

**Fix:** Read the files off disk directly. To locate them for a given run:
```bash
atx ct analysis get --id <analysis-id> --json   # → .report_paths
ls -la ~/.atxct/shared/analyses/<analysis-id>/artifacts/*/
ls -la services/<repo>/*-readiness-analysis/
```

**Caveat — `report_paths` is not complete.** On 3.9.0 it listed only the `.md` file, while the full 4-artifact bundle (`.md`, `.json`, `.html`, `.metadata.json`) was sitting in the working tree. Treat `report_paths` as a hint, not an index: always `ls` **both** locations before concluding an artifact wasn't produced.

### `list-artifacts` / `get-artifact` return "unknown command"

**Symptom:** `atx ct analysis list-artifacts` or `atx ct analysis get-artifact` fails with `error: unknown command`.

**Cause:** Both subcommands were **removed**. There is no artifact-export API to call — see above, the artifacts are already files on disk.

**Fix:** Use `analysis get` to find the paths, then read the files:
```bash
atx ct analysis get --id <analysis-id> --json   # → .report_paths
```
Then `ls` both the shared store and the repo working tree (per the caveat above) and read/copy the files with ordinary filesystem tools.

### Missing HTML or JSON alongside the markdown

**Symptom:** You found the `.md` report but believe no HTML/JSON was produced.

**Cause:** Most often you only consulted `report_paths`, which under-reports (see caveat above). On 3.9.0 a complete ARA/MOD run emits four artifacts per repo: `.md`, `.json`, `.html`, and `.metadata.json`.

**Fix:** `ls services/<repo>/*-readiness-analysis/` in the working tree before assuming anything is missing. Only if the bundle is genuinely short should you render markdown yourself (e.g. `pandoc report.md -s -o report.html`).

### Reports not found in the git repos (remote sources)

**Symptom:** After ARA/MODA on a GitHub/GitLab source, there are no report files or branches in the repos.

**Expected:** For **remote** sources nothing is committed or pushed to the repo — `ct` touches remote repo git only during a **remediation** (branch + PR). The reports still exist locally under `~/.atxct/shared/analyses/<analysis-id>/artifacts/<source>__<repo>/`. The in-tree report bundle described above is a **local-source** behavior.

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
2. Locate the report files on disk and copy them where the TD expects them:
   ```bash
   atx ct analysis get --id <ara-id> --json   # → .report_paths (incomplete — also ls)
   ls ~/.atxct/shared/analyses/<ara-id>/artifacts/*/
   ls services/<slug>/agentic-readiness-analysis/
   cp services/<slug>/agentic-readiness-analysis/<slug>-ara-report.json ./ara-reports/
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

**Symptom:** Command output shows security token error.

**Fix:**
```bash
aws sts get-caller-identity
# If expired:
aws sso login
# Then simply re-run the atx command — there is no daemon to restart.
atx ct status --health
```

### Region not supported

**Symptom:** `AWS Transform is not available in region 'us-west-2'`, or the endpoint fails to resolve at all (NXDOMAIN).

**Cause:** Only `us-east-1` resolves. A stray `AWS_REGION=us-west-2` in the environment points the CLI at a hostname that does not exist, so the failure can surface as a DNS error rather than a clean "not available" message.

**Fix:** Set the region explicitly:
```bash
export AWS_REGION=us-east-1
```
Note: `atx ct` commands use the region from your AWS config. `atx custom def exec` may require explicit region setting.

### `atx --version` reports 2.1.x instead of 3.9.0

**Symptom:** Inside Claude Code (or any Builder Toolbox-managed shell), `atx --version` prints a `2.1.x` version that doesn't match the installed CLI, which can send you chasing version-specific bugs that don't apply.

**Cause:** `atx` is shimmed by Builder Toolbox, and an inherited `$TOOLBOX_TOOL_VERSION` makes it report Toolbox's own version rather than the real `atx` version.

**Fix:** Unset it for the call:
```bash
env -u TOOLBOX_TOOL_VERSION atx --version
```

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

### Remediation fails: "repository has uncommitted changes"

**Symptom:** `remediation create` refuses to run because the target repo's working tree is dirty.

**Cause (verified 2026-08, atx 3.9.0):** A repo that is **currently being analyzed** *is* dirty, by design — `ct` rewrites the report bundle in that repo's working tree in place as the analysis progresses.

**Fix:** Wait for the analysis to reach `complete`, then retry. Alternatively, test remediation against an isolated copy of the repo registered as its own source.

**Do NOT** "fix" this by committing mid-analysis — that races the writer that is still rewriting the bundle and can leave you with a half-written report committed.

**Related:** `ct` **auto-commits** the report bundle into local-source repos, authored as `ATX Bot <checkpoint@atx.bot>`. So a *clean* tree immediately after an analysis does **not** mean nothing was written — it means the output was already committed. Check the log before concluding the analysis produced nothing:
```bash
git -C services/<repo> log --oneline --author=checkpoint@atx.bot -5
```

### `remediation create --ids` rejects ARA/MODA findings as `non_remediable`

**Symptom:** You try to remediate an ARA/MODA finding with `--ids <finding-id>` and every finding comes back `non_remediable` / there's no fix to apply.

**Cause:** ARA and MODA findings are **assessment-only** — **all** of them have `fix: null` and no bound fix-transform. The `--ids` mode only works for findings that ship a fix transform, so it can **never** work for ARA/MOD findings. This is not a data problem with your particular findings.

**Fix:** Author your own TD and use the explicit-transform mode:
```bash
atx ct remediation create --repo <src>::<repo> --source <src> \
  --transformation-name <your-td> --name "..."
```
See "Authoring a custom remediation TD" in `SKILL.md`.

### "Transformation not found in the registry" — but `custom def get` resolves it fine

**Symptom:** `remediation create --transformation-name <your-td>` fails with "Transformation not found in the registry," even though `atx custom def list` shows the TD and `atx custom def get -n <your-td>` fetches it successfully.

**Cause (verified 2026-08, atx 3.9.0):** The remediation runtime resolves transformation names against a **different catalog** than the `atx custom def` commands do. It resolves **AWS-managed** transforms (e.g. `containerize-to-eks`) but does **not** see **user-published** TDs. Publishing is not the missing step — re-publishing will not help.

**Fix:** Don't route a custom TD through `remediation create`. Execute it directly and open the PR yourself:
```bash
AWS_REGION=us-east-1 atx custom def exec -n <your-td> -p <abs-repo-path> ...
# then review the branch and raise the PR/MR manually
```

---

## Custom TD (`atx custom def`) Issues

### "AWS Transform is not available in region 'us-west-2'"

**Symptom:** `atx custom def save-draft|publish|get|exec` errors on region, even though `atx ct` commands work.

**Cause:** `atx custom def *` does not read the region from AWS config the way `atx ct` does.

**Fix:** Set `AWS_REGION` explicitly:
```bash
AWS_REGION=us-east-1 atx custom def publish -n my-td --sd ./my-td --description "..."
```

### `atx custom def get` dumped files into my working directory

**Expected behavior:** `custom def get` writes the fetched TD files (`transformation_definition.md`, etc.) into the CWD. Run it from a scratch directory, or clean up after.

### Draft TD disappeared

**Cause:** `save-draft` entries are temporary (~30-day `expiresAt`). Use `publish` for a permanent registry entry that `remediation create --transformation-name` can reference.

---

## Teardown / Environment Reset Issues

### `source remove` returns 409 (has repositories) — and exits 0 in a loop

**Symptom:** A cleanup loop "succeeds" but sources remain. Running `source remove` directly shows `API 409: Source '<x>' has repositories that still reference it.`

**Cause:** Sources can't be removed while repos reference them, and the CLI may exit 0 on the swallowed error inside a loop.

**Fix:** Delete in reverse order — repositories → findings → source. See the "Teardown" section in `references/ct-workflow.md`. Always re-list and verify counts; don't trust exit codes.

### `findings delete` refuses to delete

**Cause:** Only `dismissed` or `obsolete` findings can be deleted. Dismiss first:
```bash
atx ct findings batch-update --ids <csv> --status dismissed --reason "..."
```

### Cleanup loop fails with "read-only variable: status"

**Cause:** The shell is zsh, where `$status` is reserved/read-only.

**Fix:** Use a different variable name in polling loops (`st=$(...)` not `status=$(...)`).

---

## Publishing to Public GitHub Blocked (Amazon-managed machines)

**Symptom:** `git push` / `gh repo create --push` to a public GitHub repo is blocked: "Code Defender detected a push to an unapproved public repository." The empty repo is created but the push is rejected.

**Cause:** Amazon Code Defender DLP control on managed machines.

**Fix:** Do NOT attempt to bypass it. Options: have the user push from their own approved terminal, use a private/approved repo, or keep the ct source local. Note `ct remediation` opens PRs server-side — that path is independent of a local push.

---

## General Debugging

### Check overall system status

```bash
atx ct status
atx ct status --health
```

Shows counts for sources, repos, analyses, findings, and remediations. `--health` is the connectivity check — there is no server to ping.

### Logs

Analyses run in-process, so the logs are simply the command's own stdout/stderr. Capture them on the invocation you care about:
```bash
atx ct analysis run --type agentic-readiness --source <name> > /tmp/atx-ct-run.log 2>&1
```

Then inspect: `tail -f /tmp/atx-ct-run.log`

Per-run state and artifacts also persist under `~/.atxct/shared/analyses/<analysis-id>/`, which is worth listing when a run fails opaquely.

### Confirm which CLI you're actually running

```bash
env -u TOOLBOX_TOOL_VERSION atx --version   # plain `atx --version` misreports as 2.1.x
```
