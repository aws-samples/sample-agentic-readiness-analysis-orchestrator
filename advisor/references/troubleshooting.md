# Troubleshooting

Common failures and surprising results. Read this when something fails, or when an output looks wrong.

---

## Advisory-level failure modes

These are the ones that produce a deliverable that *looks* fine. Check them before you present anything.

### The roadmap phases are generic calendar buckets

**Symptom:** the portfolio roadmap reads "Months 0–1", "1–2", "2–4", "4–6+" with no service-level ordering, and `parallel_execution_tracks[].dependencies` is empty.

**Cause:** the portfolio dependency map is empty — `dependency_map: {"source":"inferred","dependencies":[],"foundation_services":[],"circular_dependencies":[]}`. The roll-up's primary input is `dependency_overrides`, which was not supplied, and its documented fallback reads the portfolio `findings[]` projection, which **strips `description`, `gap` and `recommendation`** — the only fields where integration prose lives.

**This is a result about your input, not about the customer's estate.** Say so.

**Fix:** run `portfolio-interapp-dependency-analysis`, which reads the **unstripped per-repo** artifacts, then supply its `closable_gaps[]` entries and re-run. And ask the customer for declared edges: ten declared edges beat a hundred inferred ones.

### A program was recommended that makes no sense for this estate

**Symptom:** an all-cloud estate gets a VMware or on-premises licensing program.

**Cause:** the program fired on a *finding* rather than on `context`. On-premises, VMware and licensing programs must trigger on portfolio or service `context` references, or on infrastructure-as-code evidence (`vsphere_*`, bare-metal configs) — **never** on findings about workloads already running on AWS.

**Fix:** check the program's `trigger_reason`. If it cites a finding about an AWS-hosted workload, drop it from the slide and note it. Also check you are reading **both** program artifacts: the portfolio JSON `recommended_actions[]` is canonical for status, the Markdown carries the narrative and programs absent from the JSON. Merge on acronym-else-name lowercased; JSON status wins.

### A zero-edge service was put in the first wave

**Symptom:** a service with no dependencies is presented as the ideal first migration.

**Cause:** a coverage grade of `None` or `Silent` was read as "independent". `None` means integrations were described but names did not resolve. `Silent` means integrations were never described. **Neither licenses the word independent** — and this misread is actively harmful, because the front of the plan is exactly where an undiscovered dependency does the most damage.

**Fix:** re-render every zero-edge service with its coverage grade attached and the placement marked provisional. For `None`, add aliases. For `Silent`, ask what that service talks to.

### A numeric portfolio improvement was claimed from one before/after

**Cause:** portfolio roll-ups are numerically unstable run-to-run. The same analysis over the same source can return materially different finding counts.

**Fix:** present portfolio deltas **categorically only**. Never claim a numeric portfolio fix from a single pair of runs.

### The draft says platform work made something agentic

**Cause:** axis drift. Platform modernization sets a **ceiling** on agentic capability and never contributes to it.

**Fix:** rewrite as a price reduction — modernization lowers the cost of every agentic rung after it and leaves the climb undone. Only a customer-declared *reimagine* intent can support an agentic-readiness increase.

---

## Connectivity

### Never start a server — there isn't one to start

**Symptom:** a command failed and you are tempted to run `atx ct server`.

**Cause:** no server is needed. `atx ct` analyses run **in-process** — the CLI does the work itself. `atx ct server` is a hidden, deprecated command that starts a daemon and **blocks the shell** until killed; in an automated flow it hangs the session outright.

**Fix:** health-check instead.

```bash
atx ct status --health
```

If the health check fails, the cause is credentials or Region. **"Server not running" is never a valid diagnosis** for any `atx ct` failure.

---

## Sources

### Discovery scan returns zero repositories

**Fix:** for local sources, `--path` must point to a **parent directory** containing repositories as subdirectories, not to a repository.

```bash
❌ atx ct source add --name x --provider local --path ./services/my-app
✅ atx ct source add --name x --provider local --path /absolute/path/to/services
```

The scanner looks for child directories containing a `.git` folder.

### `SETUP_REQUIRED`

The source exists in your account but credentials are not configured on this machine. Re-add it:

```bash
atx ct source remove --name <name>
atx ct source add --name <name> --provider <provider> --path <path>   # or --org for remote
```

### `AUTH_REQUIRED`

The token is invalid, expired, or missing scopes — GitHub needs `repo` (classic PAT), GitLab needs `api`, Bitbucket needs read for discovery and write for remediation. Re-add with a fresh token.

### Cannot remove a source (409 conflict)

Sources cannot be removed while repositories reference them. Delete the repositories first:

```bash
atx ct repository list --source <name> --json
atx ct repository delete --repo <slug> --source <name>
atx ct source remove --name <name>
```

---

## Analyses

### `INVALID_INPUT` on `analysis run`

Verify the type name: `tech-debt-quick`, `tech-debt-comprehensive`, `security`, `agentic-readiness`, `modernization-readiness`, or `custom` (which requires `--transformation-name`). Note that `rapid-techdebt-analysis` and `quick-scan` are accepted on input but the **canonical persisted value is `tech-debt-quick`** — that is what `analysis list --type <x>` filters on.

### Analysis stuck in `running`

1. `atx ct analysis get --id <id>` for per-repo status.
2. If stuck past about 40 minutes with no progress, `atx ct analysis cancel --id <id>`.
3. Re-run.

But read the next entry first — "stuck with no reports" usually is not stuck.

Note on `--wait`: it **does** exist on `analysis run` — it is just hidden from `--help`, so an absent help entry is not evidence against it. In agent workflows prefer explicit polling, so you keep control of the timeout and can report progress.

### `status: complete` but no reports, no findings, no portfolio summary

**Symptom:** on a multi-repo run, `analysis get` reads `status: complete` with `completed_at` set, but `report_paths` is `{}`, findings are empty, `portfolio_ara_summary` is `null`, and `progress` reads `{"done": 0, "total": 11}`. It looks like the run produced nothing.

**Cause: it isn't finished.** `status` flips to `complete` when the **per-repo phase** ends; the **portfolio phase** then runs for tens of minutes on the same invocation, and everything above is populated in the final record update. Measured on an 11-repo ARA: `completed_at: 20:27:42Z`, but at 20:37 the launching process was still alive (68 min elapsed) and still logging `Still analyzing portfolio-<name>... (7m elapsed)`. The run had already generated 899 findings.

**Fix — do not re-run.** Confirm it is still working, then wait.

```bash
# 1. Is the launching process alive?  (if you launched it)
ps -p <pid> -o pid,etime

# 2. Is the portfolio phase still progressing?  Line count should grow.
wc -l < <your-run-log>; sleep 60; wc -l < <your-run-log>

# 3. Have the artifacts landed yet?
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

Terminal condition for a poller: **process exit** (best), or `status` terminal **and** `report_paths` non-empty, **with a timeout** — an early failure leaves `report_paths` empty permanently, so the second form alone can hang.

**Side effect: the premature transition can swallow a real failure.** Once `status` is terminal, a portfolio-phase error cannot move it — you get `saveFn: exhausted 3 retries persisting analysis <id>: Analysis is already in terminal status COMPLETE; cannot transition`, and the run keeps `status: complete` while carrying a populated `error`. Two runs of the same ARA hitting the same persist bug ended one `failed` and one `complete`, purely on this race. **Always read `error` and `repo_errors` directly:**

```bash
atx ct analysis get --id <id> --json | jq '{status, error, repo_errors}'
```

This is the third way `status` misleads. The other two: a readiness run can read `failed` when its output is fine, and a run can read `complete` when its portfolio report is missing — recorded as a `repo_error`, which does not fail the run. **Always corroborate `status` with artifacts on disk and `findings count` before reporting an outcome.**

### `PersistFindingsError: ... repositoryId ... Member must not be null`

**Symptom:** at the very end of a multi-repo ARA:

```
PersistFindingsError: Failed to persist finding portfolio::my-portfolio::API::<hash>:
  1 validation error detected: Value at 'findings.1.member.repositoryId'
  failed to satisfy constraint: Member must not be null
```

**Cause:** portfolio *cross-cutting* findings span several repositories by definition, so they carry no single `repositoryId`. Re-running will not avoid it.

**What survives:** everything except the cross-cutting findings. The log says so explicitly — `persisted 473/473 findings before failing; preserving them in the local record` — and the full four-artifact portfolio bundle, including the `.html` and the `.json` downstream definitions consume, is already on disk, because the report is written *before* the persist step. The cross-cutting findings remain readable in `portfolio_ara_summary.cross_cutting_blockers` on the analysis record and in the portfolio report itself; they are only missing from the findings store.

**Fix:** do not re-run — read the artifacts.

```bash
atx ct analysis get --id <id> --json | jq '.portfolio_ara_summary.cross_cutting_blockers'
ls ~/.atxct/sources/*/*/runs/<id>/portfolio-*/*-analysis/
```

The run's `status` afterwards is **not deterministic** — see the entry above. Same bug, two presentations.

### Analysis completes but reports 0 findings

Report artifacts **are** written (`report_paths` non-empty) but the count is 0. If `report_paths` is empty, read the entry above first — the run is probably still going.

Causes, in order:

- repositories were not properly discovered — confirm with `atx ct repository list`;
- the analysis type does not apply (`security` requires `atx ct setup security-agent`);
- the repositories really are compliant for that type;
- your CLI is old. Re-run the installer (`curl -fsSL https://transform-cli.awsstatic.com/install.sh | bash` — **there is no `atx update` subcommand**), then re-run. Upgrading preserves registered sources, repositories and prior analyses.

### `-g`/`--configuration` not accepted

**Cause:** `-g`/`--configuration` on `analysis run` is **only valid with `--type custom`.** Built-in types reject it.

**Fix:** remove it. To steer the readiness analyses use the steering flags — `--context` (both), `--agent-scope` (ARA only), `--prefer`/`--avoid` (MOD only). Mixing a flag with the wrong type is a hard validation error, not a silent ignore.

### `schedule create --expression` is rejected

Schedules take a fixed set of recurrence keywords, not cron syntax.

```bash
atx ct schedule create --name nightly-ara --mode aws-managed --recurrence daily \
    --type agentic-readiness --sources <name> --execution-role <arn>
# also: --recurrence weekly:MONDAY   |   --recurrence monthly:1
```

`--execution-role` is required for `--mode aws-managed`; `--mode ec2|batch` needs `--stack-name` instead. The fire time is not configurable to the minute.

### "fewer than 2 valid reports" / "no portfolio ARA report found" / "no portfolio MOD report found"

**Cause: not a bug if you ran against a single repository.** Both portfolio definitions require **≥ 2 per-repo reports** to aggregate, and aggregation is **per-run** — a run only sees the reports produced within itself. Two separate single-repo runs do **not** accumulate into a two-report portfolio.

Additionally, the `bridge_summary` phase needs **both** a portfolio ARA report **and** a portfolio MOD report. Having only one is enough to fail it, even with 2+ repositories.

**Fix:** run one analysis over a source with 2+ discovered repositories (omit `--repo`), and run **both** readiness types before expecting `bridge_summary` to succeed.

### A portfolio definition found zero per-repo reports

**Cause:** the discovery walk did not follow symlinks. `ct` symlinks per-repo outputs under mangled names, so a bare recursive search finds nothing.

**Fix:** follow symlinks — `find -L`, or `os.walk(followlinks=True)`.

---

## Artifacts

### Where the report artifacts actually are

**Symptom:** after an analysis completes you do not know where to look, or `find . -name "*report*"` from the wrong directory returns nothing.

**Cause:** reports **are** on the local filesystem — in **three** places with different contents, and `report_paths` points at the thinnest one. File counts from one 11-repo ARA run:

| Location | md | json | html | meta |
|---|---|---|---|---|
| `~/.atxct/shared/analyses/<id>/artifacts/<source>__<repo>/` — where `report_paths` points | 12 | 1 | 0 | 0 |
| `~/.atxct/sources/<src>/<type>/runs/<id>/` — **the only complete copy** | 12 | 13 | 1 | 1 |
| `services/<repo>/*-analysis/` in the working tree (local sources only) | ✓ | ✓ | ✓ | ✓ |

```
~/.atxct/sources/<src>/<type>/runs/<id>/
├── <source>-<repo>-<16hex>/<type>-analysis/<repo>-{ara,mod}-report.{md,json}
└── portfolio-<name>/<type>-analysis/<name>-portfolio-{ara,mod}-report.{md,json,html,metadata.json}
```

**Fix:** glob the `sources/` tree — do not construct the path.

```bash
find ~/.atxct/sources -path "*runs/<analysis-id>/*" -type f              # everything the run produced
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/       # the portfolio bundle
atx ct analysis get --id <analysis-id> --json                            # → report_paths + portfolio_summary.report_path
```

Two reasons hand-built paths fail here: **`<type>` is the source's analysis root, not the run's type** (a modernization run can write under `sources/<src>/agentic-readiness/runs/<id>/`), and per-repo directories are slug-mangled `<source>-<repo>-<16hex>` (a sha256 prefix), not the `<source>__<repo>` form used in `shared/analyses/`.

### Pulling the full per-repo bundle

`report_paths` is **markdown-only**. For the complete bundle, glob the run tree — or, for a run executed on AWS compute, download the stored artifact:

```bash
# Always works, every compute mode — glob the run tree
ls ~/.atxct/sources/*/*/runs/<id>/portfolio-*/*-analysis/

# Managed-infrastructure runs only (atx ct remote analysis)
atx ct analysis list-artifacts --id <id> [--repo <r>] [--json]
atx ct analysis get-artifact   --id <id> --artifact-id <aid> [--output <file>]
```

**`list-artifacts` and `get-artifact` are scoped to a managed-infrastructure analysis** — they list and download the artifacts *stored* for a run executed on AWS compute (`atx ct remote analysis`). A Local-mode run stores none, so an empty listing there is expected rather than a failure; read the run tree instead. On a managed run, artifacts materialize per-repo as each repository completes, so a mid-run listing can be partial.

### The portfolio bundle is missing

**Check for absence before you assume misplacement.** The portfolio phase can terminate having written **no artifact at all**, with nothing in `repo_errors` — so hunting directories looks for a file nothing ever wrote, and finding nothing there proves nothing. Read the analysis record before you touch the filesystem:

```bash
atx ct analysis get --id <id> --json \
  | jq '{status, portfolio_summary,
         pf: .repo_errors._portfolio_ara,
         pkeys: (.report_paths|keys|map(select(startswith("_"))))}'
```

1. **`_portfolio_ara` (or `_portfolio_mod`) populated** → the inner portfolio run **failed** and its message is right there. Fix what the message says; the path is not the problem.
2. **`portfolio_summary: null`, no `_portfolio_*` key in `report_paths`, nothing in `repo_errors`** → the portfolio phase **produced nothing**. Not a path problem, and re-globbing will not find it. Confirm the run covered ≥ 2 repositories (a single-repo run legitimately produces no portfolio report), then re-run the portfolio phase.
3. **Only once those two are clean** is it a lookup problem — and then glob rather than construct:

```bash
find ~/.atxct -name '*portfolio*-report.html'                     # settles "does it exist anywhere"
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

### Missing HTML or JSON alongside a markdown report that does exist

**Cause:** the markdown you found came from a markdown-only view. `report_paths` and `~/.atxct/shared/analyses/` are effectively **markdown-only** (1 json, 0 html across a whole 11-repo run), and working trees hold **per-repo bundles only**, because no repository owns portfolio output. The portfolio `.html` and `.json` exist in exactly one place — the `sources/` run tree — **when they exist at all**, so run the absence check above before concluding a portfolio file is merely elsewhere.

```bash
ls ~/.atxct/sources/*/*/runs/<analysis-id>/portfolio-*/*-analysis/
```

Only if the bundle is genuinely short should you render markdown yourself (`pandoc report.md -s -o report.html`).

**Corollary for a failed run:** a portfolio phase that completed its report and then died persisting findings still leaves the full four-artifact bundle on disk. `status: failed` does not mean no artifacts — check before re-running.

### Reports not found in the git repositories (remote sources)

**Expected.** For **remote** sources nothing is committed or pushed to the repositories — `ct` touches remote repository git only during a **remediation** (branch + PR). The reports still exist locally under `~/.atxct/shared/analyses/<analysis-id>/artifacts/<source>__<repo>/`. The in-tree report bundle is a **local-source** behavior.

---

## Custom definitions (`atx custom def`)

### "AWS Transform is not available in region 'us-west-2'"

**Cause:** `atx custom def *` does not read the Region from AWS config the way `atx ct` does.

```bash
AWS_REGION=us-east-1 atx custom def publish -n <name> --sd definitions/custom/<name> \
  --category analysis --description "..."
```

### `atx custom def exec -n <name>` says the definition is not found

**Cause:** the name is resolved from the **registry**, not from disk, and the registry is per-account. Having the folder in your clone is not having it published, and a definition published into another account does not resolve here.

**Fix:** publish it into the account you are working in and verify, per [`td-catalog.md` §0](td-catalog.md#0-what-you-need-on-disk):

```bash
AWS_REGION=us-east-1 atx custom def publish -n <name> --sd definitions/custom/<name> \
  --category analysis --description "..."          # containerize-service: --category remediation
atx custom def get -n <name> --td "$(mktemp -d)"
```

### `atx custom def publish` rejects the source directory

**Cause:** `--sd` is validated against the schema's allowlist and anything else is a hard failure (`Unsupported file(s) or directory in … transformation definition`). Only the directory's **top-level** entries are checked, and the allowlists are wider than they look: the **SKILL** schema takes `SKILL.md` plus optional `workflow.yaml`, `references/`, `scripts/` and `summaries.md`; the **LEGACY** schema takes `transformation_definition.md` plus optional `summaries.md`, `document_references/` and `references/`.

**Fix:** read the rejected entry out of the message — it names the file. Five of the six definitions in this repository publish straight from `definitions/custom/<name>`, IAD included: `scripts/` and `summaries.md` are both allowed, and IAD's own `SKILL.md` runs `python3 -I scripts/prepare_corpus.py`, so staging it without `scripts/` would publish a definition that calls files it does not carry. Only `containerize-service` needs a staged copy, for its contributor `README.md`. See [`td-catalog.md` §0](td-catalog.md#0-what-you-need-on-disk).

### `atx custom def get` dumped files into my working directory

**Expected.** It writes the fetched definition files out, into the CWD unless you pass `--td <dir>`. Point it at a scratch directory.

### A draft definition disappeared

`save-draft` entries are temporary (roughly a 30-day expiry). Use `publish` for a permanent registry entry that `remediation create --transformation-name` can reference. The registry is also **per-account** — publish into the account the work runs in.

### `atx ct` refuses a definition it can see

The name resolves — `atx custom def list` shows it — and `ct` still rejects it:

```
Transformation definition "<name>" has no category, so it can't be used for a custom analysis.
Publish it with --category analysis to use it here.
```

**Cause (check this first):** the definition carries no `--category`, or the wrong one. `ct` gates on the tag — `analysis` for `atx ct analysis run --type custom --transformation-name <name>`, `remediation` for `atx ct remediation create --transformation-name <name>` — while `atx custom def exec -n <name>` does not look at it at all. That asymmetry is the whole trap: `--category` is optional to `publish`, so an untagged definition publishes, lists, and *execs* cleanly, and fails only on the `ct` path. The message reads `is tagged <x>` instead of `has no category` when a tag is present but wrong, and there is a mirror-image remediation wording ("…so it can't be used for remediation. Publish it with --category remediation to use it here.").

**Fix:** re-publish with the right tag — `--category analysis` for the five analysis definitions, `--category remediation` for `containerize-service` ([`td-catalog.md` §0](td-catalog.md#0-what-you-need-on-disk)).

### A published definition is "not found" by the remediation worker

**Cause (second branch, once the category is right):** the registry is tenanted by auth mode. A definition published under one mode is invisible to a worker reading the other. Note the wording differs — a tenanting miss is a genuine *not found* ("was not found in this account"), where a category miss names the definition and explains itself.

**Fix:** publish in the mode the worker reads, and verify with `atx custom def get -n <name> --td "$(mktemp -d)"` **in that mode** before depending on the name. A pass in the other mode proves nothing.

### `atx custom def exec` fails with ENOENT

Usually a path issue:

- `-p` must be an absolute path (or a valid relative path from the CWD);
- `-g file://...` must use the correct absolute path to the config;
- the CWD may have drifted — use absolute paths in automated flows.

### A custom definition cannot find its input reports

1. Verify the prerequisite analyses are truly `complete`, not just `running`.
2. **Resolve the real paths from the analysis record** rather than from any documented filename — the execution-plan definition documents a different filename pattern than the portfolio definitions emit.

```bash
atx ct analysis get --id <id> --json                            # → report_paths (markdown-only)
ls ~/.atxct/sources/*/*/runs/<id>/portfolio-*/*-analysis/       # the JSON
find ~/.atxct/sources -path "*runs/<id>/*" -name '*.json'
```

3. Check which format the definition wants: `bridge-analysis` wants **Markdown**, the execution plan wants **JSON**. A JSON-only workspace gives the bridge nothing to read.
4. Ensure `service_inventory[].path` entries match actual repository paths.

### A custom definition run hangs past 30 minutes

The execution plan's timeout is 1800000 ms. For very large portfolios raise it to 2400000 ms. If it exceeds the timeout, check for credential expiration mid-run with `aws sts get-caller-identity`.

### A run leaves you on a staging branch

**Expected.** The transform creates `atx-result-staging-*` for its git operations, and the output lands there.

```bash
git checkout <your-branch>
git merge --no-ff atx-result-staging-<timestamp>   # if you want the output on your branch
```

---

## Credentials and Region

### "The security token included in the request is invalid"

```bash
aws sts get-caller-identity
aws sso login            # if expired
atx ct status --health   # then just re-run the atx command — there is no daemon to restart
```

If credentials were refreshed but still read as expired, suspect stale credential-expiry environment variables rather than bad credentials — unset them and retry.

### Region not supported / endpoint does not resolve

**Cause:** only `us-east-1` resolves. A stray `AWS_REGION=us-west-2` points the CLI at a hostname that does not exist, so the failure can surface as a DNS error rather than a clean "not available" message.

```bash
export AWS_REGION=us-east-1 AWS_DEFAULT_REGION=us-east-1
```

---

## Remediation

### Permission errors

Remediation creates branches and PRs/MRs, so it needs write access: GitHub `repo` (full), GitLab `api`, Bitbucket `write:repository:bitbucket` and `write:pullrequest:bitbucket`. Rotate with `atx ct source update --name <name> --token <new-token>`.

### Branch created but no PR

**Expected for local sources** — there is no remote to open a PR against. Review and merge the local branch yourself:

```bash
git -C <repo-path> branch --list 'remediation-*'
git -C <repo-path> merge <branch-name>
```

### "repository has uncommitted changes"

**Cause:** a repository **currently being analyzed** *is* dirty, by design — `ct` rewrites the report bundle in that repository's working tree in place as the analysis progresses.

**Fix:** wait for the analysis to reach true completion, then retry. Alternatively, test remediation against an isolated copy registered as its own source.

**Do NOT** "fix" this by committing mid-analysis — that races the writer still rewriting the bundle and can leave a half-written report committed.

**Related:** `ct` **auto-commits** the report bundle into local-source repositories, authored `ATX Bot <checkpoint@atx.bot>`. So a *clean* tree immediately after an analysis does **not** mean nothing was written — it means the output was already committed.

```bash
git -C services/<repo> log --oneline --author=checkpoint@atx.bot -5
```

### `remediation create --ids` rejects readiness findings as `non_remediable`

**Cause:** ARA and MOD findings are **assessment-only** — **all** of them have `fix: null` and no bound fix transform. The `--ids` mode only works for findings that ship one, so it can **never** work for readiness findings. This is not a data problem with your particular findings.

**Fix:** use the explicit-transform mode.

```bash
atx ct remediation create --repo <src>::<repo> --source <src> \
  --transformation-name <your-td> --name "..."
```

### Remediation fails to push a branch, with a Python traceback

**Cause:** on machines where pyenv's Python has a broken `hashlib` (blake2b/blake2s `ValueError`), `git push` fails during remediation.

**Fix:** export `PYENV_VERSION=system` in the environment running `atx ct`.

---

## Teardown

### `source remove` returns 409 — and exits 0 inside a loop

**Cause:** sources cannot be removed while repositories reference them, and the CLI may exit 0 on the swallowed error inside a loop.

**Fix:** delete in reverse order — repositories → findings → source. See the teardown section in [`ct-operations.md`](ct-operations.md). Always re-list and verify counts; do not trust exit codes.

### `findings delete` refuses

Only `dismissed` or `obsolete` findings can be deleted. Dismiss first:

```bash
atx ct findings batch-update --ids <csv> --status dismissed --reason "..."
```

### "read-only variable: status"

**Cause:** the shell is zsh, where `$status` is reserved and read-only.

**Fix:** use a different variable name in polling loops — `st=$(...)`, not `status=$(...)`.

---

## General debugging

```bash
atx ct status             # account-wide counts: sources, repos, analyses, findings, remediations
atx ct status --health    # the connectivity check — there is no server to ping
atx ct schema             # the full command tree as machine-readable JSON
readlink -f "$(command -v atx)"   # which CLI you are actually running
```

`atx --version` reports an internal build string that does not match the install-path version — **resolve the install path instead.**

Analyses run in-process, so the logs are the command's own stdout and stderr. Capture them on the invocation you care about:

```bash
atx ct analysis run --type agentic-readiness --source <name> > /tmp/atx-ct-run.log 2>&1
tail -f /tmp/atx-ct-run.log
```

Per-run state and artifacts also persist under `~/.atxct/shared/analyses/<analysis-id>/`, which is worth listing when a run fails opaquely.
