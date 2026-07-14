---
name: portfolio-agentic-readiness-analysis
description: Aggregates per-repo ARA reports into portfolio-level cross-cutting analysis
type: managed
---

# Portfolio Agentic Readiness Analysis

> **This is a managed AWS transformation definition.** It runs automatically as the portfolio-aggregation stage of `atx ct analysis run --type agentic-readiness`. The full definition is maintained in the AWS Transform service and versioned independently. This file documents the interface and behavior for reference.

## Analysis Type

Portfolio stage of `atx ct analysis run --type agentic-readiness` — runs AFTER all per-repo agentic-readiness analyses complete. Do not run it before the per-repo reports exist; it consumes them as input.

## What it evaluates

Aggregates all per-repo ARA reports into a portfolio-level view: readiness-profile distribution across the estate, cross-cutting BLOCKERs and RISKs, an executive dashboard, and a portfolio remediation roadmap.

It also produces the **Agentic Program Recommendations** step: based on portfolio-wide findings, it recommends the three ARA agentic anchor programs (AI DLC, AXE, Innovation EBA) plus any triggered `[ARA]` / `[ARA+MOD]` programs from the shared **AWS Program & GTM Library** (`references/program-library.md`). Recommendations are capped at 3–5, grouped **Funded Programs → Engagement Models**, sequenced Assessment → Funding → Execution → Optimization, and never expose internal numeric maturity scores.

## References

- `references/program-library.md` — the AWS Program & GTM Library. Loaded at runtime during the program-recommendation step; it is the authoritative catalog of signal patterns, exclusions, qualification criteria, prioritization, grouping, status filtering, and the reasoning checklist.

## Output artifacts

- Portfolio: artifact key `_portfolio_ara`, name `report` — stored in the ct artifact store (`atx ct analysis get-artifact --id <analysis-id> --repo _portfolio_ara --name report`)
- On local sources: portfolio report files may also be written alongside the per-repo `services/<repo>/agentic-readiness-analysis/` outputs
- JSON output emits `recommended_actions[]` (program entries with `id`, `name`, `acronym`, `type`, `group`, `status`, `trigger_reason`); MD output renders them under `## Recommended Actions`

## Relationship to per-repo TD

The per-repo TD (`agentic-readiness-analysis`) generates individual reports. This portfolio TD aggregates them across the portfolio and is the ONLY place engagement-program recommendations are produced. Run per-repo first, then portfolio.
