# TODO — Open Work

Only TD/code items that are **programmatically actionable** live here. Every item below can be picked up and executed end-to-end without waiting on a human decision. Docx threads, reply-only items, pending scope decisions, and standing CR hygiene rules are tracked elsewhere (review docs, Asana, contributor guide).

**Last verified:** May 6, 2026 — DATA-Q1 tiered rubric (B1/B2/B3) shipped on `main` (commit `51248df`). Refactor reduced portfolio DATA-Q1 BLOCKERs from 14 → 7 by replacing the binary "no formal classification = BLOCKER" rule with a tiered model that evaluates API response scoping, access control differentiation, and formal classification metadata independently.

---

## 🚀 Phase H — JSON Report Output

**Source:** GianFranco feedback post-v3. Portfolio TDs currently re-parse markdown tables to extract scores, pathway triggers, findings, and tech stack. Fragile, slow, regex-prone. A structured JSON sidecar alongside each markdown report fixes accuracy, speed, and validation in one move.

- [ ] **H-1 — Define JSON schemas.**
  - `modernization-assessment/report-schema.json` (JSON Schema draft 2020-12)
  - `agentic-readiness-assessment/report-schema.json` (severity enum, not numeric score; tiered DATA-Q1 must represent B1/B2/B3 resolutions)
  - Both have `"schema_version": "1.0.0"` at top level
  - Cover metadata, scores (N/A as `{"status":"NA","reason":"..."}`), pathways, findings, tech stack, quick agent wins

- [ ] **H-2 — Assessor TDs emit JSON sidecars.**
  - MOD TD writes `{repo}-mod-report.md` AND `{repo}-mod-report.json`
  - ARA TD writes `{repo}-ara-report.md` AND `{repo}-ara-report.json`
  - JSON is canonical; markdown is derived.

- [ ] **H-3 — Portfolio TDs consume JSON with markdown fallback.**
  - Portfolio MOD and Portfolio ARA prefer `*.json`, fall back to `*.md`
  - Both emit portfolio-level JSON sidecars
  - Bridge TD reads both portfolio JSON sidecars directly

- [ ] **H-4 — Power doc + consolidation.**
  - Update `agentic-assessment-orchestrator/POWER.md` to document the JSON sidecar output
  - Consolidation step moves both `.md` and `.json` into `v{N}-full-assessment/`

- [ ] **H-5 — Validate emitted JSON against schema for each v5 example report.**

### Risk notes

- **Double-write drift** — MD and JSON must stay in sync. JSON is the single source of truth; MD is derived.
- **Backward compat** — v2/v3/v4/v5 markdown-only reports MUST keep working. JSON is "preferred when present," not required.
- **Schema stability** — external tooling (dashboards, Jira, Taskei) will depend on this. Breaking changes bump schema version.

---

## 📝 MOD TD — Calibration Wins (v3/v4 reviewer feedback)

Validated against current MOD TD: none of these are in the TD yet.

- [ ] **C-9 — INF-Q9 RTO/RPO inputs.** Current INF-Q9 evaluates multi-AZ but doesn't mention RTO/RPO. Add to why-it-matters + look-for: "HA design is driven by RTO/RPO requirements; a system with a 4-hour RPO and 1-hour RTO has different HA demands than one with 24-hour RPO." Small edit.

- [ ] **C-10 — DATA-Q3 commercial licensing + vendor lock-in signal.** DATA-Q3 currently covers engine versions but not licensed-engine cost/lock-in. Add a Score 2/1 modifier when commercial-licensed engines (Oracle, SQL Server, commercial MongoDB) are detected. Modifies existing rubric without adding question count. (The "Move to Open Source" pathway already uses commercial-engine signals from DATA-Q4 + INF-Q2 — this closes the same loop in DATA-Q3 itself.)

- [ ] **C-11 — INF-Q5 hybrid networking.** Score 3/4 look-for doesn't name hybrid networking resources. Add: Site-to-Site VPN, Direct Connect, Transit Gateway, Cloud WAN. Small edit.

- [ ] **C-12 — Reconcile on-prem handling with AWS-targeting scope.** The A1 scope statement says "targets workloads on AWS" but rubric rows (INF-Q1 Score 1, INF-Q2 Score 1) correctly penalize on-prem. Refine A1 to clarify the assessment evaluates modernization *for AWS migration* — current workload may be on AWS, on-prem, or other clouds. Keep the on-prem = Score 1 signals. **Depends on D3** for the no-IaC case.

> **Note on organizational readiness:** Proposed questions on team ownership, change management, skills, and governance are already queued on the Asana board for verification before being added to the TD. Not tracked here until they land.

---

## 🏗 MOD TD — Architectural Expansion

- [ ] **D3 — External inventory channel for non-IaC / non-AWS workloads.** MOD currently assumes the target repo carries infrastructure signal via IaC (Terraform, CloudFormation, CDK, Helm). This misses target customers whose current workload runs on-prem, on Azure/GCP/bare-metal, or lacks IaC — infrastructure is described externally in Modelize IT, Cloudockit, CAST Imaging, or a customer-provided inventory doc. Introduce an alternative infrastructure-signal channel so the assessor can ingest an external inventory report (JSON or Markdown) and feed Step 1 discovery with the same rigor IaC gets.

  External inventory signal should:
  - Feed the same file inventory entries (compute, databases, networking, messaging) that IaC would feed
  - Feed the surface flags (Step 1.6) — `has_persistent_data_store`, `has_at_rest_data_surface`, etc.
  - Produce accurate findings for on-prem workloads (Score 1 on INF-Q1/Q2 if on-prem compute/databases are detected)

  Scope expansion (new input channel), not rubric softening. **Affects:** Step 1 (Discovery), N/A mapping, Surface-flag detection (Step 1.6), "no IaC found" fallback behavior.

---

## What's left, at a glance

| Category | Count | Items |
|----------|-------|-------|
| 🚀 Phase H JSON | 5 | H-1..H-5 |
| 📝 MOD calibration wins | 4 | C-9, C-10, C-11, C-12 |
| 🏗 MOD architectural | 1 | D3 |
| **Total remaining** | **10** | |

**Next concrete step:** C-9 + C-11 are low-risk why-it-matters / look-for edits that can ship in a single small CR. C-10 + C-12 are DATA-Q3 / scope-statement rewrites that should go in their own CR. D3 is the big one — scope it before committing to Phase H.

---

## Tracked elsewhere (not here)

- **G1 (IaC governance question), G2 (resilience testing coverage)** — pending scope decisions in docx threads 32 and 51. Add to this file once a direction is chosen.
- **Organizational readiness questions** — queued on the Asana board for verification.
- **Docx reply threads** — tracked in the review docs.
- **Standing CR hygiene** (match on FIND text, verify question count ripple, JSON schema validation before shipping) — belongs in a contributor guide / PR template, not a recurring todo.
