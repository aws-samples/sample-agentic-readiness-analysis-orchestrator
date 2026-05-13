# Reconciliation Gate

The mandatory gate between per-repo execution and any portfolio TD invocation. Read this when implementing the orchestration step that bridges individual reports into portfolio aggregation, or when troubleshooting why a portfolio TD is not seeing all the per-repo reports.

> **🚪 Why the gate exists.** Portfolio TDs do filesystem-based discovery. They glob for `*-ara-report.json`, `*-mod-report.json`, and `*-bpmn-opportunity-report.json` under the workspace, validate the JSON schema, and aggregate. Any artifact at the wrong path, with the wrong filename, missing companion files, or stranded on an ATX staging branch will be either silently excluded or picked up incorrectly. The orchestrator MUST reconcile workspace state before invoking any portfolio TD.

---

## When the Gate Runs

- **Once after all per-repo subagents return** (before Portfolio ARA launches)
- **Once before each subsequent portfolio TD invocation** (between Portfolio ARA → MOD → BAO → Bridge)

The gate enforces three checks in order. **All checks must pass — abort with an actionable error if any fails.**

---

## Check A — Branch Consolidation

### Why

Each ATX execution forks a per-execution staging branch (`atx-result-staging-<timestamp>-<id>`) and lands the four-artifact bundle on that branch, then returns to the original branch. After all per-repo subagents complete, all artifacts must be visible on a single branch before portfolio TDs run. Otherwise, the portfolio TD's filesystem discovery sees only the branch tip's view, missing the staging-branch artifacts.

### Two Patterns

**Operator-driven (recommended for repos under user control):**

Before invoking the orchestrator, the operator creates a portfolio-run branch in each repo they own:

```bash
git -C <repo_path> checkout -b portfolio-run-<date>
```

ATX staging branches fork from this branch. The operator merges them back at the end. **The orchestrator does not manipulate git state on operator-owned repos.**

**Orchestrator-managed (cloned repos only):**

For repos cloned by the orchestrator (those with `repository_url` and a non-existent `path`), the orchestrator owns the branch fully. After per-repo subagents complete, the orchestrator MUST:

1. List staging branches in each cloned repo:
   ```bash
   git -C <repo_path> -P branch --list 'atx-result-staging-*'
   ```
2. For each staging branch, fast-forward-merge it into the working branch (`main` or the portfolio-run branch):
   ```bash
   git -C <repo_path> merge --ff-only <staging_branch>
   ```
   If a non-fast-forward is required, abort with a clear error — this indicates a parallel-execution race that should not occur with per-repo serialization.
3. After all merges, verify the working tree is clean and on the expected branch:
   ```bash
   git -C <repo_path> -P status --short
   ```
4. Optionally delete the merged staging branches (only after successful merge):
   ```bash
   git -C <repo_path> branch -d <staging_branch>
   ```

### Failure Mode

If any cloned repo's working tree is not clean after the consolidation step, abort with:

```
Reconciliation failed: {repo} has uncommitted changes after staging branch merge. Manual intervention required.
```

---

## Check B — Filename and Path Standardization

### Why

Each portfolio TD expects artifacts at canonical paths with canonical names. Any deviation (wrong nesting, wrong slug, missing prefix) makes the artifact invisible to discovery.

### Canonical Paths

| Per-Repo TD | Canonical artifact path (relative to repo root) | Slug source |
|---|---|---|
| ARA | `{repo_path}/agentic-readiness-assessment/{slug}-ara-report.{md,json,html,metadata.json}` | `slug = lowercase(repo.name)` from portfolio config |
| MOD | `{repo_path}/modernization-assessment/{slug}-mod-report.{md,json,html,metadata.json}` | Same slug as ARA |
| BAO | `{repo_path}/bpmn-opportunity-assessment/{slug}-bpmn-opportunity-report.{md,json,html,metadata.json}` | Same slug as ARA |

### Slug Derivation Rule

```
slug = lowercase(repo.name)
       with any character not in [a-z0-9_-] replaced by '-'
```

**Always derive from the portfolio config — never from the repo's filesystem basename.** The basename can mismatch the configured `name` (e.g., `MonoToMicroLegacy` directory under a `unishop-monolith` config name).

### Reconciliation Logic

For each repo and each TD that ran on it:

1. Compute the expected canonical path from the slug rule above
2. **If the canonical `.md` exists** → record SUCCESS for that TD on that repo
3. **If the canonical `.md` does not exist**, search the repo for stray artifacts:
   ```bash
   find {repo_path} -maxdepth 4 -type f \
       -name '*-ara-report.md' \
       -o -name '*-mod-report.md' \
       -o -name '*-bpmn-opportunity-report.md'
   ```
   For each stray artifact, compare its slug to the expected slug:
   - **Slug matches** → MOVE the full four-file bundle (md, json, html, metadata.json) into the canonical directory
   - **Slug mismatches** → ABORT with the manual-classification error (no auto-rename)

   ```
   Reconciliation failed: stray artifact at {found_path} does not match any configured repo slug. Manual classification required.
   ```
4. After move, re-verify the canonical `.md` exists. If still missing, mark this TD's run as FAILED — no portfolio aggregation will include it.

### Common Stray Patterns (auto-resolved when slug matches)

| Observed location | Cause |
|---|---|
| `{repo}/{slug}-mod-report.md` | Report landed at repo root instead of `modernization-assessment/` subfolder |
| `{repo}/services/{slug}/{slug}-ara-report.md` | Working-directory confusion produced extra nesting |
| `{repo}/agentic-readiness-assessment/{wrong-slug}-ara-report.md` | Slug mismatch — ABORT, do not auto-rename |

---

## Check C — Four-Artifact Bundle Completeness

### Why

Every per-repo and portfolio TD's contract requires emitting four files: `.md`, `.json`, `.html`, `.metadata.json`. The portfolio TDs consume the **`.json`** (the canonical contract) — if it's missing, the report is invisible to aggregation regardless of whether the `.md` exists.

### Logic

For each canonical `.md` present, verify all three companions exist alongside it:

```bash
ls {td_folder}/{slug}-{type}-report.json 2>/dev/null
ls {td_folder}/{slug}-{type}-report.html 2>/dev/null
ls {td_folder}/{slug}-{type}-report.metadata.json 2>/dev/null
```

### Severity Levels

| Missing artifact | Action |
|---|---|
| `.json` | **ABORT.** Portfolio aggregation requires `.json`. Re-run the TD against the repo. |
| `.html` | Log warning, continue. Webapp dashboard will be impaired. |
| `.metadata.json` | Log warning, continue. Version compatibility checks will be impaired. |

For `.json` missing:

```
Reconciliation failed: {repo}/{td} has .md but missing .json. Portfolio aggregation requires .json. Re-run this TD against the repo.
```

For `.html` or `.metadata.json` missing:

```
Bundle incomplete for {repo}/{td}: missing {.html|.metadata.json}. Continuing.
```

---

## Reconciliation Summary Output

After all checks pass, Kiro emits a single-line per-repo summary to the user before launching any portfolio TD:

```
✓ Reconciliation passed for portfolio "ecommerce-platform-v2" (5 repos, 10 individual reports)
  - unishop-monolith: ARA ✓, MOD ✓
  - aws-microservices: ARA ✓, MOD ✓
  - books-api: ARA ✓, MOD ✓
  - local-monolith: ARA ✓, MOD ✓
  - eks-saas-gitops: ARA ✓, MOD ✓
  Branch: main (5 repos consolidated, 10 staging branches merged and pruned)
```

If any check fails, Kiro emits the specific error and **does not launch any portfolio TD**. Partial portfolio reports look authoritative but exclude entire services silently — they are worse than no portfolio report at all.

---

## Gate Between Portfolio TDs

The same three-check structure applies between each portfolio TD invocation, but applied to the just-emitted portfolio bundle rather than per-repo bundles:

- **Check A:** Did the portfolio TD's staging branch merge cleanly into the working branch?
- **Check B:** Is the portfolio report at `{td_folder}/{portfolio_name}-portfolio-{type}-report.md`? Move strays if needed (slug = portfolio_name).
- **Check C:** Are all four artifacts present? `.json` missing → ABORT the chain; do not run the next portfolio TD.

If any portfolio TD fails its gate, abort the chain. The completed reports remain valid, but downstream TDs that depend on this one's `.json` cannot proceed reliably.
