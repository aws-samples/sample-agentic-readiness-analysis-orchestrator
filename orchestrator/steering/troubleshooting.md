# Troubleshooting

Common errors and fixes. Read this when an assessment fails, when reports go missing, or when the user reports unexpected behavior.

---

## Per-Repo Assessment Fails

**Symptoms:** `atx custom def exec` returns a non-zero exit code, or the expected `.md` report does not appear.

**Diagnostic:**
1. Check ATX CLI is installed:
   ```bash
   atx --version
   ```
2. Verify the TD is in the registry:
   ```bash
   atx custom def list | grep <td_name>
   ```
3. Confirm the `transformation_definitions` block in `portfolio-config.yaml` matches exactly what was published (case-sensitive)
4. Confirm you're running with the correct working directory and `-p` path
5. Confirm the repo has the files the TD expects (source code, build configs, etc.)
6. To see verbose errors, run interactively (drop `-x -t`):
   ```bash
   atx custom def exec -n <td_name> -p <repo_path> -g file://<config>
   ```

---

## Portfolio TD Cannot Find Per-Repo Reports

**Symptoms:** Portfolio assessment runs but reports show "0 services aggregated" or are missing entire repos.

**Root causes (in order of frequency):**
1. Per-repo `.json` artifact missing (only `.md` was emitted) — portfolio TDs require `.json`
2. Reports landed at non-canonical paths (e.g., repo root instead of `modernization-assessment/`)
3. Reports stranded on ATX staging branches that were never merged into the working branch
4. Slug mismatch — the report's filename slug doesn't match the configured `repo.name`

**Fix:**
1. Run the Reconciliation Gate manually (see `steering/reconciliation-gate.md`)
2. For each repo:
   ```bash
   # Verify the canonical .md exists
   ls {repo}/agentic-readiness-assessment/{slug}-ara-report.md
   ls {repo}/modernization-assessment/{slug}-mod-report.md

   # Verify all four artifacts are present
   ls {repo}/agentic-readiness-assessment/{slug}-ara-report.{md,json,html,metadata.json}
   ```
3. If `.md` is at the wrong path, move the full bundle (md/json/html/metadata.json) to the canonical path
4. If `.json` is missing, re-run that per-repo TD
5. If artifacts are on a staging branch:
   ```bash
   git -C <repo_path> -P branch --list 'atx-result-staging-*'
   git -C <repo_path> merge --ff-only <staging_branch>
   ```

---

## ATX Command Times Out

**Symptoms:** `executeBash` returns timeout/exit-code -1 with no clear error, "Thinking..." spinner runs for a long time.

**Context:** This is expected behavior. Per-repo TDs typically take 5–15 minutes; portfolio TDs 15–30 minutes; very large repos can exceed both.

**Fix (in order):**
1. **Check the report file first** — the command may have completed successfully even if executeBash timed out:
   ```bash
   ls {repo}/agentic-readiness-assessment/*-ara-report.md
   ls {repo}/modernization-assessment/*-mod-report.md
   ls agentic-readiness-assessment/*-portfolio-ara-report.md
   ls modernization-assessment/*-portfolio-mod-report.md
   ```
2. If the report exists, the assessment succeeded — the No-Polling Contract treats this as SUCCESS regardless of executeBash exit status
3. If the report is missing, re-run with extended timeout (e.g., 2400000ms for very large repos)
4. For very large repositories, consider running interactively (drop `-x`) to monitor progress

> **Important:** Do NOT retry inside a subagent. Recovery is the operator's call. Concurrent ATX runs against the same repo cause staging-branch divergence.

---

## Subagent Becomes Impatient

**Symptoms:** Subagent makes multiple `ls`/`find`/`cat` calls during what should be a single ATX wait, then reports false-negative failures or attempts to retry.

**Cause:** The subagent violated the No-Polling Contract.

**Fix:**
1. Stop the panicking subagent
2. **Do not try to salvage partial state from the panicked run** — staging branches may be in an undefined state
3. Re-launch the TD freshly with a clean executeBash call and the configured timeout (1200000 ms per-repo, 1800000 ms portfolio)
4. Verify the subagent issues exactly one executeBash for the ATX command and exactly one filesystem check after it returns

See `POWER.md` for the full No-Polling Contract.

---

## Bridge TD Fails

**Symptoms:** Portfolio ARA and Portfolio MOD complete, but Bridge TD errors with "missing report" or schema validation errors.

**Causes:**
1. One of the upstream portfolio TDs failed and only one portfolio report exists — Bridge requires both ARA and MOD
2. Bridge config references the wrong paths (must be relative to workspace root)
3. Portfolio BAO report path was passed in but the file doesn't exist
4. Old `bpmn_opportunity_report_paths[]` field used (deprecated — use the singular `portfolio_bao_report_path` instead)

**Fix:**
1. Verify both portfolio reports exist at canonical paths:
   ```bash
   ls agentic-readiness-assessment/{portfolio_name}-portfolio-ara-report.md
   ls modernization-assessment/{portfolio_name}-portfolio-mod-report.md
   ```
2. If only one exists, re-run the missing portfolio TD before retrying Bridge
3. Update the bridge ATX config to use `portfolio_bao_report_path` (singular) for the aggregated BAO portfolio report

> Bridge failure does NOT invalidate the ARA and MOD portfolio reports. The bridge is supplementary.

---

## Configuration Validation Errors

**Symptoms:** The orchestrator rejects `portfolio-config.yaml` before launching any TD.

**Diagnostic:**
1. Validate against the JSON schema:
   ```bash
   ajv validate -s portfolio-config.schema.json -d portfolio-config.yaml
   ```
2. Common required-field errors:
   - `portfolio_name` is missing or empty
   - `assessment_type` is missing or not one of the four valid values
   - `transformation_definitions` is missing one or more required TD names for the chosen `assessment_type`
   - A `repositories[]` entry is missing `name` or `path`

3. Common enum errors:
   - `agent_scope` is not `read-only` or `write-enabled`
   - `repo_type` is not one of `application`, `infrastructure-only`, `deployment-config`, `monorepo`, `library`
   - `priority` is not `P0`, `P1`, or `P2`
   - `dependency_overrides[].type` is not `sync`, `async`, `shared_db`, or `shared_infra`

4. Common structural errors:
   - `preferences.prefer` and `preferences.avoid` must be string arrays, not bullet lists
   - `service_inventory[]` and `dependency_overrides[]` in portfolio TD configs must be structured YAML object arrays, not free-text strings

See `steering/portfolio-config.md` for the full schema reference.

---

## Preferences Not Applied

**Symptoms:** MOD recommendations include technologies in the `avoid` list or omit ones in the `prefer` list.

**Causes:**
1. `preferences` was placed in an ARA config (preferences are MOD-only and silently ignored by ARA TDs)
2. Per-repo `avoid` correctly overrode global `prefer` — this is intended behavior (see merge rules in `steering/portfolio-config.md`)
3. The recommended technology is, in the TD's judgment, the only viable fit despite the `avoid` directive — preferences are guidance, not guarantees

**Fix:**
1. Confirm preferences appear only in MOD configs (per-repo MOD and portfolio MOD)
2. Review the merged preferences in the actual ATX config Kiro generated (look at `.atx-config-{slug}-mod.yaml` before cleanup)
3. If you need a hard enforcement, the TD documentation may have a stricter mode — but most TDs treat preferences as soft guidance

---

## ATX CLI Not Found

**Symptoms:** `atx: command not found`

**Fix:**
1. Install AWS Transform CLI: https://docs.aws.amazon.com/transform/
2. Verify installation:
   ```bash
   atx --version
   ```
3. Check `PATH` includes the AWS Transform CLI binary location
4. Restart your terminal after installation

---

## ATX Publish Fails Mid-Batch

**Symptoms:** Publishing multiple TDs in parallel produces errors like:
- `Error: ENOENT: no such file or directory, unlink '/Users/.../tmp/transformation.tar'`
- `Error: Failed to upload the transformation: Status code 400 from aws-transform-custom-...`

**Cause:** The atx CLI uses a shared tar staging path (`~/tmp/transformation.tar`). Concurrent `atx custom def publish` invocations overwrite each other's staging files.

**Fix:** Always publish TDs **serially**, never in parallel:

```bash
atx custom def publish -n td1 --sd ./td1 --description "..."
atx custom def publish -n td2 --sd ./td2 --description "..."
atx custom def publish -n td3 --sd ./td3 --description "..."
```

Do not parallelize publish commands.

---

## Reports Land on a Staging Branch and Look "Missing"

**Symptoms:** ATX exit code 0, but `ls` shows no report. `git status` shows you're on `atx-result-staging-<timestamp>`.

**Cause:** ATX staged the artifacts and committed them to a fresh staging branch but failed to switch back to the original branch (or you switched manually mid-run).

**Fix:**
1. Check current branch:
   ```bash
   git -C <repo_path> branch --show-current
   ```
2. If on a staging branch, check out the working branch:
   ```bash
   git -C <repo_path> checkout main      # or your portfolio-run branch
   ```
3. Merge the staging branch:
   ```bash
   git -C <repo_path> merge --ff-only atx-result-staging-<timestamp>
   ```
4. Verify reports are now visible:
   ```bash
   ls <repo_path>/agentic-readiness-assessment/
   ```

---

## Working Tree Has Uncommitted Changes Before Run

**Symptoms:** ATX warns "uncommitted changes" or stash conflicts.

**Cause:** ATX stashes local changes onto the staging branch as part of its workflow. Stale uncommitted changes from a previous run can confuse this process.

**Fix:**
1. Either commit your local changes:
   ```bash
   git -C <repo_path> add -A
   git -C <repo_path> commit -m "WIP before assessment"
   ```
2. Or stash them yourself:
   ```bash
   git -C <repo_path> stash push -m "before assessment"
   ```
3. Then re-run the TD

Do NOT use `git reset --hard` or `git clean -fd` — these can destroy uncommitted work.
