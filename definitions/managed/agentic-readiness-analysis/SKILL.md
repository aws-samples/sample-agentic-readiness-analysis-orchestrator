---
name: agentic-readiness-analysis
description: Evaluates whether systems are ready to be safely called by AI agents - covering APIs, identity, state management, human-in-the-loop, and observability
type: managed
---

# Agentic Readiness Analysis

> **This is a managed AWS transformation definition.** It runs automatically via `atx ct analysis run --type agentic-readiness`. The full definition is maintained in the AWS Transform service and versioned independently. This file documents the interface and behavior for reference.

## Analysis Type

`atx ct analysis run --type agentic-readiness`

## What it evaluates

Whether each repository's systems are ready to be safely called by AI agents. Findings cover APIs and machine-readable interfaces, identity and authentication, state management and idempotency, human-in-the-loop controls, and observability. Each repo is assigned a readiness profile (`Agent-Ready`, `Pilot-Ready`, `Pilot-Ready (Safety Concerns)`, `Remediation Required`, `Not Agent-Integrable`) with BLOCKER/RISK/INFO findings per category.

This per-repo report intentionally does NOT recommend AWS engagement programs (MAP, EBA, AppMod, AI Assessment, SHIP, ACP, etc.). Program eligibility depends on cross-repo scope, customer segment, ARR, and partner context that a single-repo analysis does not have — those recommendations are produced by the portfolio TD.

## Output artifacts

- Per-repo: `ara` (format: markdown) — stored in the ct artifact store
- On local sources: also written to `services/<repo>/agentic-readiness-analysis/<repo>-ara-report.{md,json,html,metadata.json}`

## Relationship to portfolio TD

This per-repo TD generates individual reports. The portfolio TD (`portfolio-agentic-readiness-analysis`) aggregates them across the portfolio and produces engagement-program recommendations from the shared AWS Program & GTM Library. Run per-repo first, then portfolio.
