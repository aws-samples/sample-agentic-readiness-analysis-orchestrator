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

| Step | Who | What |
|------|-----|------|
| Live discovery | **You** | `./demo-scripts/01-live-discovery-push.sh` (3 repos → 4) |
| Run analysis | **Claude** | "run ARA on pricing-cgi" / "run MODA on pricing-cgi" |
| Show findings | **You** | Console → Findings tab |
| Remediate | **Claude** | "containerize shipping-api" (uses containerize-to-eks) |
| Show the diff | **You** | `git -C harness/fixtures/portfolio/legacy-shipping-api diff main` (local branch) |

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
- **Remediation uses managed `containerize-to-eks`** (custom user TDs are not resolvable by the ct remediation runtime as of 2026-07).
- **Reports are NOT markdown-only, and `analysis list-artifacts`/`get-artifact` no longer exist.** The full bundle (`.md`, `.json`, `.html`, `.metadata.json`) is on local disk in the source-scoped run tree — the only complete copy, and the only place portfolio `.html`/`.json` exist. `report_paths` on the analysis record is the markdown-only view. Glob, never construct: the segment after the source name is the *source's* analysis root (a MOD run lands under `.../agentic-readiness/runs/<id>/`) and per-repo dirs are slug-mangled `<source>-<repo>-<16hex>`.
  ```bash
  ls ~/.atxct/sources/*/*/runs/<id>/portfolio-*/*-analysis/   # portfolio bundle (open the .html)
  find ~/.atxct/sources -path "*runs/<id>/*" -type f          # everything a run produced
  ```
- **`atx --version` misreports inside Claude Code** (shows Builder Toolbox's `2.1.x`). Use `env -u TOOLBOX_TOOL_VERSION atx --version`. Needs **≥ 3.9.0** — 3.7.0 silently produced 0 findings.
- **pricing-cgi is always held back** for the live-discovery moment (deleted from ct after setup's discovery; reappears on re-scan).
- **ct discovery does NOT follow symlinks** — local sources must contain real repo dirs.
