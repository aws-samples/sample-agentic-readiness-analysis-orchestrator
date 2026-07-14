---
name: portfolio-modernization-readiness-analysis
description: Aggregates per-repo MOD reports into portfolio-level roadmap and cross-cutting analysis
type: managed
---

# Portfolio Modernization Readiness Analysis

> **This is a managed AWS transformation definition.** It runs automatically as the portfolio-aggregation stage of `atx ct analysis run --type modernization-readiness`. The full definition is maintained in the AWS Transform service and versioned independently. This file documents the interface and behavior for reference.

## Analysis Type

Portfolio stage of `atx ct analysis run --type modernization-readiness` — runs AFTER all per-repo modernization-readiness analyses complete. Do not run it before the per-repo reports exist; it consumes them as input.

## What it evaluates

Aggregates all per-repo MOD reports into a portfolio-level view: an aggregated pathway plan across the seven modernization pathways, cross-cutting analysis of unified `High`/`Medium`/`Low` findings, classification-tier distribution, and a portfolio modernization roadmap.

It also produces the **AWS Programs & Engagement Recommendations** step: based on portfolio-wide findings, it recommends triggered `[MOD]` / `[ARA+MOD]` programs (MAP, OLA, AppMod, EBA, VMCCO, SHIP, etc.) from the shared **AWS Program & GTM Library** (`references/program-library.md`). Recommendations are capped at 3–5, grouped **Funded Programs → Engagement Models**, sequenced Assessment → Funding → Execution → Optimization, and never expose the internal 1–4 maturity score — only severity/classification language.

## References

- `references/program-library.md` — the AWS Program & GTM Library. Loaded at runtime during the program-recommendation step; it is the authoritative catalog of signal patterns, exclusions, qualification criteria, prioritization, grouping, status filtering, and the reasoning checklist.

## Output artifacts

- Portfolio: artifact key `_portfolio_mod`, name `report` — stored in the ct artifact store (`atx ct analysis get-artifact --id <analysis-id> --repo _portfolio_mod --name report`)
- On local sources: portfolio report files may also be written alongside the per-repo `services/<repo>/modernization-readiness-analysis/` outputs
- JSON output emits `recommended_actions[]` (program entries with `id`, `name`, `acronym`, `type`, `group`, `status`, `trigger_reason`); MD output renders them under `## Recommended Actions`

## Relationship to per-repo TD

The per-repo TD (`modernization-readiness-analysis`) generates individual reports. This portfolio TD aggregates them across the portfolio and is the ONLY place engagement-program recommendations are produced. Run per-repo first, then portfolio.
