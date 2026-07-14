# AWS-Managed Transformation Definitions

These four transformation definitions (TDs) are the **AWS-managed definitions that run inside `atx ct`** (AWS Transform Continuous Modernization). Unlike the custom TD in `../custom/`, you never invoke them by name via `atx custom def exec` — the `ct` server executes them internally when you run:

```bash
atx ct analysis run --type agentic-readiness      # per-repo ARA + portfolio ARA
atx ct analysis run --type modernization-readiness # per-repo MOD + portfolio MOD
```

## Source of truth

This directory is the **source of truth** for the managed TDs: **what's on `main` goes to prod.** Changes land here via PR, and the `main` version of each definition is what the AWS Transform service runs. Each folder is a publishable package (see [`scripts/publish-td.sh`](../../scripts/publish-td.sh)).

## The four TDs

| TD | Stage | Description |
|---|---|---|
| [`agentic-readiness-analysis`](agentic-readiness-analysis/SKILL.md) | Per-repo | Evaluates whether systems are ready to be safely called by AI agents — covering APIs, identity, state management, human-in-the-loop, and observability |
| [`modernization-readiness-analysis`](modernization-readiness-analysis/SKILL.md) | Per-repo | Scans portfolios for cloud-native maturity gaps and maps findings to AWS modernization pathways |
| [`portfolio-agentic-readiness-analysis`](portfolio-agentic-readiness-analysis/SKILL.md) | Portfolio | Aggregates per-repo ARA reports into portfolio-level cross-cutting analysis |
| [`portfolio-modernization-readiness-analysis`](portfolio-modernization-readiness-analysis/SKILL.md) | Portfolio | Aggregates per-repo MOD reports into portfolio-level roadmap and cross-cutting analysis |

## Execution order

Per-repo TDs run first (one report per discovered repository); the portfolio TDs run after all per-repo reports exist and aggregate them. `atx ct` sequences this automatically within a single `analysis run`.

## `references/program-library.md`

The two portfolio TDs each carry a `references/program-library.md` — the **AWS Program & GTM Library**. It is loaded at runtime by the portfolio TDs during their program-recommendation step and is the authoritative catalog of AWS programs (MAP, OLA, AppMod, EBA, SHIP, AI DLC, AXE, Innovation EBA, etc.), including signal patterns, exclusions, qualification criteria, selection rules (cap at 3–5, group Funded Programs → Engagement Models), and the reasoning checklist.

Engagement-program recommendations are produced **only** by the portfolio TDs — never by the per-repo TDs, which lack the cross-repo and customer-segment context to qualify programs.

> **⚠️ The program-library is intentionally duplicated** in both portfolio TD folders (`portfolio-agentic-readiness-analysis/references/` and `portfolio-modernization-readiness-analysis/references/`). This is because each folder is a **self-contained publishable package** — when you publish a TD to the ATX registry via `--sd <folder>`, only the files inside that folder are included. There is no cross-package reference mechanism at runtime; the agent loads `references/program-library.md` from within its own package.
>
> **If you update the program library, you must update it in both places.** The two copies must stay identical. A quick check:
> ```bash
> diff definitions/managed/portfolio-agentic-readiness-analysis/references/program-library.md \
>      definitions/managed/portfolio-modernization-readiness-analysis/references/program-library.md
> ```
> If this produces output, one copy is stale — sync before publishing.

## Directory structure

```
managed/
├── README.md
├── agentic-readiness-analysis/
│   └── SKILL.md
├── modernization-readiness-analysis/
│   └── SKILL.md
├── portfolio-agentic-readiness-analysis/
│   ├── SKILL.md
│   └── references/
│       └── program-library.md
└── portfolio-modernization-readiness-analysis/
    ├── SKILL.md
    └── references/
        └── program-library.md
```
