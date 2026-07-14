# Demo Harness — AWS Transform Continuous Modernization

All scripts default to **LOCAL mode** (no GitHub, no Code Defender, no scopes).
Pass `--remote` for the GitHub mode.

## Quick reference

```
demo-scripts/
├── 00-full-setup.sh           # Bake full env: server + source + discovery + ARA + MODA + export
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
| Show the diff | **You** | `git -C sample-legacy-portfolio/legacy-shipping-api diff main` (local branch) |

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
  cd ../sample-legacy-portfolio/legacy-shipping-api
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

- **ct server must run with `PYENV_VERSION=system AWS_REGION=us-east-1`** — the setup script handles this. Without `PYENV_VERSION=system`, pyenv's Python 3.13.2 (broken hashlib blake2b) crashes git push inside the server.
- **Local mode remediation creates a local branch** (no PR) — the ct Console still shows it, and you demo the diff in terminal.
- **Remote mode needs Code Defender self-attest** or the server-side push fails.
- **Remediation uses managed `containerize-to-eks`** (custom user TDs are not resolvable by the ct remediation runtime as of 2026-07).
- **Reports are markdown-only in the artifact store** — render locally if browser view needed.
- **pricing-cgi is always held back** for the live-discovery moment (deleted from ct after setup's discovery; reappears on re-scan).
- **ct discovery does NOT follow symlinks** — local sources must contain real repo dirs.
