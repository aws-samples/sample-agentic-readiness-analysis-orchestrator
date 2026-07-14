---
name: modernization-readiness-analysis
description: Scans portfolios for cloud-native maturity gaps and maps findings to AWS modernization pathways
type: managed
---

# Modernization Readiness Analysis

> **This is a managed AWS transformation definition.** It runs automatically via `atx ct analysis run --type modernization-readiness`. The full definition is maintained in the AWS Transform service and versioned independently. This file documents the interface and behavior for reference.

## Analysis Type

`atx ct analysis run --type modernization-readiness`

## What it evaluates

Cloud-native maturity gaps in each repository, mapped to the seven AWS modernization pathways (`Move to Cloud Native`, `Move to Containers`, `Move to Open Source`, `Move to Managed Databases`, `Move to Managed Analytics`, `Move to Modern DevOps`, `Move to AI`). Findings carry unified severity (`High`/`Medium`/`Low`), effort ratings, and per-category `severity_status` (`Ready`/`Needs Work`/`Critical`) and `score_rating` (`Mature`/`Partial`/`Needs Work`/`Not Ready`). The internal 1–4 maturity score is never exposed.

The per-repo report's "programs" tab / Recommended Actions render modernization pathways and pathway-mapped learning materials only — NOT AWS engagement programs (MAP, OLA, AppMod, etc.). Engagement-program recommendations are produced exclusively by the portfolio TD from the shared AWS Program & GTM Library.

## Output artifacts

- Per-repo: `mod` (format: markdown) — stored in the ct artifact store
- On local sources: also written to `services/<repo>/modernization-readiness-analysis/<repo>-mod-report.{md,json,html,metadata.json}`

## Relationship to portfolio TD

This per-repo TD generates individual reports. The portfolio TD (`portfolio-modernization-readiness-analysis`) aggregates them across the portfolio and produces engagement-program recommendations from the shared AWS Program & GTM Library. Run per-repo first, then portfolio.
