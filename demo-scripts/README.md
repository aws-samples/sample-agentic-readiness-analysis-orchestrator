# Demo Harness — AWS Transform Continuous Modernization

All scripts default to **LOCAL mode** (no GitHub, no Code Defender, no scopes).
Pass `--remote` for the GitHub mode.

## Quick reference

```
demo-scripts/
├── 00-full-setup.sh           # Bake full env: health + source + discovery + ARA + MODA + export
├── 00-push-repos.sh           # [remote only] Push 3 pre-baked repos to org (from YOUR terminal)
├── 01-live-discovery-push.sh  # Live act: pricing-cgi "appears" (3 repos → 4)
├── 02-reset-live-discovery.sh # Reset the live-discovery beat for rehearsal
├── 99-full-reset.sh           # Nuke everything: ct + local state (+ GitHub with --remote)
└── README.md
```

## Full cycle — LOCAL (default)

```bash
./demo-scripts/99-full-reset.sh      # 1. reset (if re-running)
./demo-scripts/00-full-setup.sh      # 2. bake env (~45 min unattended)
# 3. ready for demo!
```

No prerequisites beyond `atx` CLI + AWS creds (us-east-1). Nothing GitHub-related.

## During the demo (with Claude)

### First: load the skill

The **Claude** rows below only work if Claude is running as the orchestrator. The skill in
[`../orchestrator/`](../orchestrator/) is what teaches it the `atx ct` behavior this demo depends
on — which commands still exist, when a run is actually finished, and where the reports really
live. Without it Claude will improvise, and the failure modes here are ones that look like
success (see "Key facts" below).

Install it once, then start Claude Code from the project root:

```bash
# from the project root
mkdir -p ~/.claude/skills/ara-moda-orchestrator
cp -R orchestrator/SKILL.md orchestrator/references ~/.claude/skills/ara-moda-orchestrator/
```

Re-copy after pulling — an out-of-date installed copy is worse than none, because it confidently
uses commands that were removed. Verify the loaded copy is current:

```bash
diff -q orchestrator/SKILL.md ~/.claude/skills/ara-moda-orchestrator/SKILL.md \
  && echo "skill is current" || echo "STALE — re-copy before demoing"
```

Then confirm it engaged before you present. Ask Claude *"what analyses can you run?"* — it should
name ARA, MODA and the Execution Plan, and know that portfolio aggregation needs ≥2 repos. If it
asks what `atx ct` is, the skill did not load. You can also just say **"use the
ara-moda-orchestrator skill"**.

### The run of show

| Step | Who | What |
|------|-----|------|
| Live discovery | **You** | `./demo-scripts/01-live-discovery-push.sh` (3 repos → 4) |
| Run analysis | **Claude** | "run ARA on pricing-cgi" / "run MODA on pricing-cgi" |
| Show findings | **You** | Console → Findings tab |
| Show the report | **Claude** | "open the portfolio report" → the `.html` in the sources run tree |
| Remediate | **Claude** | "containerize shipping-api" (uses the TD you published — see below) |
| Show the diff | **You** | `git -C harness/fixtures/portfolio/legacy-shipping-api diff main` (local branch) |

Two things to know before you present, so a healthy run doesn't look like a broken one:

- **A single-repo analysis produces no portfolio report** — aggregation needs ≥2 repos, and the
  run still spends ~13 min invoking the portfolio TD before declining. Expected, not a bug.
- **"failed" on a multi-repo ARA usually still gave you everything you're about to show.** See
  Key facts. Don't abandon the demo on that word.

## Rehearsal loop (just the live-discovery beat)

```bash
./demo-scripts/01-live-discovery-push.sh     # pricing-cgi appears
# ... rehearse ...
./demo-scripts/02-reset-live-discovery.sh    # back to 3 repos
```

## Remote mode (optional — real GitHub PRs)

Only if you want the "PR appears in GitHub" story. Extra prerequisites:

- `gh` CLI authenticated (`repo`, `admin:org`; `delete_repo` for resets)
- GitHub org `YOUR-GITHUB-ORG` exists
- Code Defender self-attest per repo — must run **inside a repo dir with origin set**:
  ```bash
  cd ../harness/fixtures/portfolio/legacy-shipping-api
  git remote add origin https://github.com/YOUR-GITHUB-ORG/legacy-shipping-api.git
  git-defender self-attest --reason 1 --url "https://github.com/YOUR-GITHUB-ORG/legacy-shipping-api.git"
  # repeat per repo
  ```

```bash
./demo-scripts/99-full-reset.sh --remote
./demo-scripts/00-push-repos.sh                    # from YOUR terminal (Code Defender)
./demo-scripts/00-full-setup.sh --remote
./demo-scripts/01-live-discovery-push.sh --remote
./demo-scripts/02-reset-live-discovery.sh --remote
```

## Key facts

- **There is no server to start.** Analyses run in-process. `atx ct server` still exists but is deprecated and hidden — starting it just blocks a shell on `:8081` for no benefit. The scripts only health-check with `atx ct status --health`.
- **`status: complete` is not a terminal signal.** On a multi-repo run it flips when the *per-repo* phase ends, while the portfolio phase runs on for tens of minutes — during which `report_paths` is `{}` and findings are empty, so the run looks like it produced nothing. `00-full-setup.sh` waits for `status` terminal **and** `report_paths` non-empty. Don't "fix" a run that looks empty; check `ls ~/.atxct/sources/*/*/runs/<id>/portfolio-*/*-analysis/` first.
- **An ARA that reports `failed` is usually still fine.** Any ≥2-repo run emitting a cross-cutting blocker trips a service-side persist bug (`repositoryId ... must not be null`). Reports and per-repo findings are already saved; only the cross-cutting findings miss the store, and they remain readable in `portfolio_ara_summary.cross_cutting_blockers`. The setup script continues in this case rather than aborting the demo.
- **Local mode remediation creates a local branch** (no PR) — the ct Console still shows it, and you demo the diff in terminal.
- **Remote mode needs Code Defender self-attest** or the server-side push fails.
- **You must publish the remediation TD yourself — there is no built-in containerization transform.** ARA/MOD findings are assessment-only (`fix: null`), so `--ids` can never remediate them; remediation always runs a TD you name. Any TD works, and `remediation create` **does** resolve user-published ones. Publish it, then confirm the exact name resolves in the demo's account **and** region — TD names go stale (drafts expire, TDs get deleted, the registry is shared). `containerize-to-eks`, named in earlier versions of these docs, no longer resolves at all.
  ```bash
  AWS_REGION=us-east-1 atx custom def publish -n <my-td> --sd <path-to-td-dir> --description "..."
  cd "$(mktemp -d)" && AWS_REGION=us-east-1 atx custom def get -n <my-td>   # ✓ = ready to demo
  ```
  Then: `atx ct remediation create --repo <src>::<repo> --source <src> --transformation-name <my-td> --name "containerize" --local` (`--local` for local sources → local branch, no PR).
- **Reports are NOT markdown-only, and `analysis list-artifacts`/`get-artifact` no longer exist.** The full bundle (`.md`, `.json`, `.html`, `.metadata.json`) is on local disk in the source-scoped run tree — the only complete copy, and the only place portfolio `.html`/`.json` exist. `report_paths` on the analysis record is the markdown-only view. Glob, never construct: the segment after the source name is the *source's* analysis root (a MOD run lands under `.../agentic-readiness/runs/<id>/`) and per-repo dirs are slug-mangled `<source>-<repo>-<16hex>`.
  ```bash
  ls ~/.atxct/sources/*/*/runs/<id>/portfolio-*/*-analysis/   # portfolio bundle (open the .html)
  find ~/.atxct/sources -path "*runs/<id>/*" -type f          # everything a run produced
  ```
- **`atx --version` misreports inside Claude Code** (shows Builder Toolbox's `2.1.x`). Use `env -u TOOLBOX_TOOL_VERSION atx --version`. Needs **≥ 3.9.0** — 3.7.0 silently produced 0 findings.
- **pricing-cgi is always held back** for the live-discovery moment (deleted from ct after setup's discovery; reappears on re-scan).
- **ct discovery does NOT follow symlinks** — local sources must contain real repo dirs.
