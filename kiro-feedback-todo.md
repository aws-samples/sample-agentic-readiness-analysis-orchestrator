# TODO — Open Work

Only items that are still **open and actionable** live here. Everything shipped, rejected, reply-only, or deferred is in `kiro-feedback-archive.md` for CR and reviewer traceability.

**Last verified:** Apr 30, 2026 — B3, F5, F6, C-1, C-2 shipped on `fix/ara-calibration` (commits `7040e7f`, `cfe3a04`). Both TDs republished (MOD `3g1ipb3idj99eltldz4nmlp3`, ARA `3g1ipe93e5d2wb6n5d4yqaf9`). Next step is the 31-repo ARA v5 re-run.

---

## 🚀 High Priority — JSON Report Output (Phase H)

**Source:** GianFranco feedback post-v3. Current portfolio TDs re-parse markdown tables to extract scores, pathway triggers, findings, tech stack. Fragile, slow, regex-prone. A structured JSON sidecar alongside the markdown fixes accuracy, speed, and validation in one move.

### Scope

- [ ] **H-1 — Define JSON schema for MOD report.**
  - Metadata (repo_name, date, repo_type, service_archetype, priority, tags, resolved preferences)
  - Scores (overall, per-category, per-question with N/A marked explicitly via `"status": "NA", "reason": "..."`)
  - Pathways (per-pathway: triggered | not-triggered | not-applicable + trigger evidence)
  - Findings (per-question: score, finding text, gap text, recommendation, evidence list)
  - Technology stack (languages, databases, compute, IaC, CI/CD, messaging)
  - Quick Agent Wins (detected prerequisites + suggested patterns)
  - `"schema_version": "1.0.0"` at top level
  - Store as `modernization-assessment/report-schema.json` (JSON Schema draft 2020-12)

- [ ] **H-2 — MOD TD: emit JSON sidecar alongside markdown.**
  - New "Output" subsection in the Report Template section
  - Assessor writes both `{repo-name}-mod-report.md` AND `{repo-name}-mod-report.json`
  - Same data, different representation. JSON is canonical; markdown is derived.

- [ ] **H-3 — Portfolio MOD TD: consume JSON with markdown fallback.**
  - Step 1 (Discovery): prefer `*-mod-report.json`, fall back to `*-mod-report.md`
  - Step 3 (Parsing): `JSON.parse` directly when available
  - Backward compat — v2-era reports must keep working

- [ ] **H-4 — ARA symmetry.**
  - Define `agentic-readiness-assessment/report-schema.json` (severity enum replaces numeric score)
  - ARA TD emits `{repo-name}-ara-report.json`
  - Portfolio ARA TD consumes JSON with markdown fallback

- [ ] **H-5 — Bridge TD: consume portfolio JSON sidecars.**
  - Portfolio ARA TD and Portfolio MOD TD both emit portfolio-level JSON sidecars
  - Bridge TD reads both JSON files directly

- [ ] **H-6 — Power documentation.**
  - Update `agentic-assessment-orchestrator/POWER.md` to mention JSON sidecar
  - Update consolidation: move both `.md` and `.json` into `v{N}-full-assessment/`

- [ ] **H-7 — Validate schema against v3 reports.**
  - Parse v3 example reports against schema; flag any markdown fields the schema misses

### Phase H Commit Strategy

| Commit | Scope | Message |
|--------|-------|---------|
| H1 | H-1 (schemas) | `feat(assessment-schemas): define JSON schemas for MOD, ARA, and portfolio reports` |
| H2 | H-2 (MOD emits) | `feat(mod-td): emit structured JSON sidecar alongside markdown report` |
| H3 | H-3 (Portfolio MOD consumes) | `refactor(portfolio-mod-td): consume JSON sidecars with markdown fallback` |
| H4 | H-4 (ARA symmetry) | `feat(ara-td,portfolio-ara-td): JSON sidecar emit + consume with markdown fallback` |
| H5 | H-5 (Bridge) | `refactor(bridge-td): consume portfolio JSON sidecars` |
| H6 | H-6 (Power) | `docs(orchestrator-power): document JSON sidecar in output structure` |

### Risk Notes

- **Double-write drift** — MD and JSON must stay in sync. Treat JSON as single source of truth; MD is derived.
- **Backward compatibility** — every portfolio TD MUST keep the markdown path working. JSON is "preferred when present", not required.
- **Schema stability** — external tooling (dashboards, Jira, Taskei) will depend on this. Breaking changes bump schema version.
- **N/A representation** — N/A is a state, not a score. Explicit in the schema.

### Unlocks

- Dashboard widgets consume JSON directly (`dashboard/modernization.html`)
- Programmatic diffs between portfolio runs (v3 vs v4)
- External integrations (Jira, Taskei) one HTTP call away
- CI validation — JSON schema check in the TD-edit CR pipeline

---

## 📝 v3/v4 Reviewer Feedback (new triage — from quick-scripts/feedback-updates)

Surfaced by the 19 new threads in MOD v3 (Damilola) and v4 (Saurabh, Malathi, Pedro, Jeff, RP, Kevin). Cross-referenced against ARA v2.1 docx feedback. Some are clear TD wins, some are docx/reply-only, and one is a genuine architectural expansion.

### 🏗 Architectural expansion (future direction)

- [ ] **D3 — External inventory channel for non-IaC / non-AWS workloads.**
  MOD assumes the target repo carries infrastructure signal via IaC (Terraform, CloudFormation, CDK, Helm). This works for AWS-native repos but misses a meaningful slice of target customers whose **current workload runs on-prem, on Azure/GCP/bare-metal, or lacks IaC entirely** — infrastructure is described externally in tools like **Modelize IT, Cloudockit, CAST Imaging, or a customer-provided inventory document**. The scoring intent is preserved: **on-prem = low score because the migration opportunity is real**, but we need the *data* to assess it. Plan: introduce an alternative infrastructure-signal channel so the assessor can ingest an external inventory report (format TBD — JSON/Markdown) and feed Step 1 discovery with the same rigor it applies to discovered IaC. External inventory signal should:
  - Feed the same file inventory entries (compute, databases, networking, messaging) that IaC would feed
  - Feed the surface flags (Step 1.6) — `has_persistent_data_store`, `has_at_rest_data_surface`, etc.
  - Let the assessor produce *accurate* findings for on-prem workloads (Score 1 on INF-Q1/Q2 if on-prem compute/databases are detected — because moving them to managed compute/databases is the modernization recommendation)
  This is a scope expansion (new input channel), not a rubric softening. The rubric still penalizes on-prem — we just need the data to see it.
  **Affects:** Step 1 (Discovery), N/A mapping, Surface-flag detection (Step 1.6), and the assessor's "no IaC found" fallback behavior.

### 🔧 MOD TD — clear calibration wins (from v3/v4 reviewer threads)

- [ ] **C-8 — Explicit organizational-readiness out-of-scope statement.**
  Raised by **Damilola (v3 #1)** and **Pedro Aceves (v4 #9)** — both independently asked about People/Organizational readiness. Pedro specifically: "Hardest modernization blockers are org-level. Even a couple questions about team ownership would help." Current MOD Summary/Objective doesn't explicitly acknowledge this is out of scope. Fix: add a one-paragraph "Organizational readiness (team ownership, change management, skills, governance) is out of scope — covered by MAA / Learning Needs Assessment (LNA) / org-level readiness frameworks" note to the MOD Summary. Point reviewers at the right companion assessment. No new questions.

- [ ] **C-9 — INF-Q9 RTO/RPO inputs** (Damilola v3 #2).
  INF-Q9 currently evaluates multi-AZ but doesn't explicitly mention RTO/RPO as inputs shaping the expected HA topology. Fix: add RTO/RPO mention in INF-Q9 why-it-matters and look-for — e.g., *"HA design is driven by RTO/RPO requirements; a system with a 4-hour RPO and 1-hour RTO has different HA demands than one with 24-hour RPO."* Small why-it-matters + look-for edit.

- [ ] **C-10 — DATA-Q3 commercial licensing + vendor lock-in + 3P integrations.**
  Raised by **Damilola (v3 #3)** AND **Saurabh Sharma (v4 #3)** — both hit the same gap: DATA-Q3 covers engine versions but not licensed-engine cost/lock-in signal. Saurabh specifically: licensed software (Oracle, SQL Server, commercial MongoDB, .NET Framework) should decrease score. Fix options: (a) add a Score 2/1 modifier in DATA-Q3 when commercial-licensed engines are detected, or (b) add to APP-Q1 look-for (already covers modern .NET vs .NET Framework), or (c) new commercial-software-lock-in question. Lean (a) — modifies existing rubric without adding question count.

- [ ] **C-11 — INF-Q5 hybrid networking** (Damilola v3 #4).
  INF-Q5 Scores 3/4 don't explicitly mention hybrid networking scenarios (Site-to-Site VPN, Direct Connect, Transit Gateway, Cloud WAN) despite these being common enterprise patterns. Fix: extend INF-Q5 Score 3/4 look-for to name hybrid networking resources. Small edit.

- [ ] **C-12 — Reconcile on-prem handling with AWS-targeting scope** (Malathi v4 #6).
  Malathi flagged an apparent inconsistency: A1 scope statement says "targets workloads on AWS" but rubric rows like INF-Q1 Score 1 include "on-prem" as a penalty case. The intent is correct — **on-prem is low-score because it IS the modernization opportunity** — but the scope statement reads as if on-prem is out of scope. Fix: refine the A1 scope statement to clarify the assessment *evaluates modernization readiness for AWS migration*, where the current workload may be on AWS (evaluating further modernization), on-prem, or on other clouds (evaluating migration to AWS). Keep the on-prem = Score 1 signals on INF/DATA questions — they correctly drive migration recommendations. **Depends on D3** for the non-IaC case: if no IaC AND no external inventory is provided, the assessor cannot confirm on-prem infrastructure and should surface "insufficient signal — provide external inventory per D3" rather than guessing Score 1 from absence.

### 📬 Reply-only items (no TD change — respond in docx threads)

Most of Jeff Escott's v4 comments and Saurabh Sharma v4 #1/#4 are questions or integration ideas, not TD changes:

- [ ] **REPLY-1 — Saurabh v4 #1:** "Can this be integrated into AI-DLC process?" — RP already replied "yes, absolutely." React/confirm in thread.
- [ ] **REPLY-2 — Saurabh v4 #4:** "S3 data source support in the demo" — not a TD issue, tool-demo concern. Acknowledge in thread.
- [ ] **REPLY-3 — Malathi v4 #5:** "But this says on-prem/multi-cloud out of scope?" — reply with A1 scope statement + D3 direction.
- [ ] **REPLY-4 — Pedro v4 #7:** "How do we determine increased win rate is the assessment vs partner/customer maturity?" — attribution question. Point at MAP outcome studies.
- [ ] **REPLY-5 — Pedro v4 #8:** "Move consolidation-value prop higher in doc." — docx-structural, not TD. Action in the docx.
- [ ] **REPLY-6 — Jeff Escott v4 #10-15:** six threads, all reply-only (RP/Kevin/Lucas replies already exist for most). Bulk close.

### 🤔 Customization decision (deferred)

- [ ] **D4 — Per-org scale calibration** (Saurabh v4 #2).
  Saurabh asked for per-org 1-4 scale calibration (different orgs have different expectations of what Score 3 means). Archetype calibration handles part of this (stateless-utility vs orchestrator expectations differ). Decide: (a) document that archetype is the calibration dimension and customization beyond that is out of scope, or (b) extend to explicit org-dimension calibration (additional plan context field). Lean (a).

### ARA — already covered (no action needed)

ARA v3/v4 feedback analysis shows all Part A/B items shipped, R1-R9 shipped, no *new* TD items from v3/v4 reviewers. Remaining ARA items are docx replies only — already tracked in **ARA-P0.1** and **ARA-P0.2** above.

**Commit strategy for the new C-items:**
| Commit | Scope | Message |
|--------|-------|---------|
| C8+C9+C11 | Low-risk why-it-matters + look-for edits | `docs(mod-td): C-8 org-readiness scope, C-9 RTO/RPO in INF-Q9, C-11 hybrid networking in INF-Q5` |
| C10 | DATA-Q3 rubric enhancement | `refactor(mod-td): C-10 commercial licensing + vendor lock-in in DATA-Q3` |
| C12 (after D3 decision) | On-prem rubric audit | `refactor(mod-td): C-12 reconcile on-prem rubric rows with AWS-targeting scope` |
| D3 | External inventory channel | `feat(mod-td): D3 external infrastructure inventory channel for non-IaC targets` |

---

## ⚠️ Pre-flight (any TD edit pass)

- [ ] **P0.1 — Clean working tree.** `git status` clean, then `git checkout -b feedback/<branch>`.
- [ ] **P0.2 — Read target section end-to-end** before the edit.
- [ ] **P0.3 — Decide on N5 / N6 scope (G1/G2).** Both propose new TD questions (IaC governance; ops resilience testing). New questions change question count and ripple into N/A mappings and category score math.

---

## 🤔 MOD TD — Phase G Scope Decisions (pending P0.3)

- [ ] **G1 — IaC governance as a new INF question** (Thread 32 / N5).
  Scope change: affects question count (11→12 INF), category score math, N/A mappings. Settle via P0.3 before execution.

- [ ] **G2 — Operations gaps — load testing, chaos, synthetics, metrics definition** (Thread 51 / N6).
  Options: (a) new OPS question covering resilience testing, (b) extensions across OPS-Q3/Q4/Q7 rubrics, (c) defer to future TD version. Settle via P0.3.

**Commit G (if adopted):** `feat(mod-td): add IaC governance question and resilience testing coverage (G1-G2)`

---

## 🤖 ARA TD — Remaining Pre-flight

- [ ] **ARA-P0.1 — Reconcile question numbering.** Analysis doc says "AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User" — actual TD has this at AUTH-Q4. Map both in CR description when replying to C11/C31.
- [ ] **ARA-P0.2 — Retrieve docx anchors for C9 and C13.** Both need comment-position lookup before response.

---

## 🔍 ARA-R Verification (post-recalibration)

All 9 ARA-R items shipped on `fix/ara-calibration`. Canary (tqdm, hapi-fhir, umami) passed. Portfolio-level verification pending.

- [ ] **V-R1 — Re-run zg-cmp portfolio** with recalibrated TD (31 non-canary repos). Expected: DATA-Q1 BLOCKER count drops from 30 → under 10. AUTH-Q6 and DATA-Q2 RISK-SAFETY drop from 31–34 → single digits for non-data repos.
- [ ] **V-R2 — Spot-check hapi-fhir.** Must still score BLOCKER on DATA-Q1 (PHI-handling) and keep RISK-SAFETY on DATA-Q2/Q6. Recalibration must not under-flag real PII systems. *(Canary confirmed Apr 29; re-verify in full v5 run.)*
- [ ] **V-R3 — Spot-check Graylog2 + umami** (observability/analytics repos that do handle user data). Must keep RISK-SAFETY on DATA-Q6.
- [ ] **V-R4 — Verify portfolio ARA trigger logic** isn't affected. Check `portfolio-agentic-readiness/transformation_definition.md` doesn't reference rubric text verbatim.

---

## 🔍 Verification (pre-CR)

- [ ] **V1 — Grep stale terms after edits land:**
  - `compute tiers` — 0 hits required (already clean)
  - `App Mesh` — 0 hits in MOD and ARA TDs (both already clean)
  - `primary database` / `Primary database` — 0 expected hits (B2 shipped)
  - `in IaC` — unchanged (R2 rejected, stays IaC)
- [ ] **V2 — Spot-check reworked rubrics** (INF-Q3, APP-Q3, APP-Q4 after B3; INF-Q7 after F6; INF-Q11 after F5; APP-Q1 after C-1) for coherent 1→4 progression.
- [ ] **V3 — Cross-check portfolio TD.** `portfolio-modernization/transformation_definition.md` references question IDs only. Re-verify no rubric text drift.
- [ ] **V4 — Cross-check example reports.** Flag as stale in CR if any scores shift after recalibration.
- [ ] **V5 — Rubric-count changes.** If G1/G2 add new questions, update Summary counter, category math, N/A mappings.
- [ ] **V6 — Phase H schema check.** Validate emitted JSON against `report-schema.json` for each TD's example report.

---

## 📦 Wrap-up (per CR)

- [ ] **W1 — Final review.** `git status` + `git -P diff --stat`.
- [ ] **W2 — Raise CR** with:
  - Link to `feedback-mod-action.md`, `kiro-feedback-changes.md`, `mod-feedback-analysis.md`
  - Rejection rationale for MOD R1/R2/R4/R5, ARA R1-R3 (from archive)
  - Phase F / G / H status (shipped vs deferred)
  - Reopened threads addressed (analysis-C10 ✅, C13 ✅ partial via F2, C23 ✅)
- [ ] **W3 — Reply in doc threads** for reply-only items (see archive).

---

## Risk Notes

- **Line numbers drift** — match on FIND text, not line numbers.
- **Phase G changes question count** — update Summary counter, category math, N/A mappings before shipping.
- **JSON schema stability (Phase H)** — once external tooling depends on it, breaking changes bump schema version.
- **Part 3 scope discipline** — if pressed to include docx-only items in TD CR, hold the line.
- **C-7 risk** — MOD surface-flag calibration parallels ARA R1/R6. Same "don't under-flag real data-handling systems" risk applies. V-R2-style spot checks required.

---

## What's left, at a glance

| Category | Count | Items |
|----------|-------|-------|
| 🚀 Phase H JSON | 7 | H-1..H-7 |
| 📝 v3/v4 reviewer feedback | 6 TD + 6 reply | D3, C-8, C-9, C-10, C-11, C-12 + REPLY-1..6 + D4 decision |
| ⚠️ Pre-flight | 3 | P0.1..P0.3 |
| 🤔 MOD scope decisions | 2 | G1, G2 |
| 🤖 ARA pre-flight | 2 | ARA-P0.1, ARA-P0.2 |
| 🔍 ARA-R Verification | 4 | V-R1..V-R4 (run zg-cmp 31-repo ARA v5) |
| 🔍 Verification | 6 | V1..V6 |
| 📦 Wrap-up | 3 | W1..W3 |
| **Total remaining** | **40** | |

**Next concrete step:** V-R1 — run `./run-assessments.sh` for 31 non-canary repos (ARA + MOD against the republished TDs), then re-run `scan-rubric-quality.py` to confirm DATA-Q1 BLOCKER, AUTH-Q6 RISK-SAFETY, INF-Q2 Score 1, and SEC-Q2 Score 1 concentrations all drop.
