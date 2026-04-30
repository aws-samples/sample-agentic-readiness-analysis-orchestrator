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

## 🔬 V3 Calibration Follow-ups

Surfaced by the v2-vs-v3 comparison and the Apr 30 cross-portfolio rubric scan. Keep in mind for the next TD iteration or assessment run.

- [ ] **C-3 — INF-Q11 narrative doesn't say "application and IaC pipelines".**
  E4 landed in the question text, but v3 report findings still read as application-pipeline-centric. If reviewers want the phrasing in the output, the rubric rows or why-it-matters would need the explicit "application and IaC" framing — not just the question header.

- [ ] **C-4 — `assessment_date` in Portfolio Assessment Inventory uses frontmatter, not run date.**
  v3 portfolio MOD inventory shows stale dates (2025-07-17 for unishop, 2026-04-27 for others) because the aggregator pulls `assessment_date` from the individual report's frontmatter rather than file mtime or run timestamp. Fix in the Portfolio MOD TD: use file mtime (or inject a run timestamp) for inventory dates. Also affects Portfolio ARA.

- [ ] **C-5 — Broaden test coverage in next portfolio run.**
  Two TD edits landed but didn't get exercised in v3:
  - **A13 MCP awareness clause** — no repo in v3 exposes MCP surfaces.
  - **E2/M18 S3 File Gateway note** — no repo has the on-prem migration scenario that triggers DATA-Q1 Score 2 with the File Gateway note.
  Add one MCP-adjacent repo and one on-prem-migration repo to the next sample portfolio config so these edits get exercise.

- [ ] **C-6 — MOD SEC-Q5 Score 1/2/3 boundary needs review (post-v4-scan).**
  The cross-portfolio scan (`scan-rubric-quality.py` run Apr 30, 2026) showed SEC-Q5 Score 2 absorbing 33 repos with mixed maturity — v2/monolith (CloudFormation NoEcho parameters), v2/eks-saas-gitops (SSM Parameter Store for Gitea admin password), and repos that still have plaintext credentials alongside *some* secret management. Score 2 is not differentiating "has partial secret management" from "has partial secret management plus remaining plaintext." Rewrite the 1/2/3 rubric rows so Score 1 = plaintext anywhere, Score 2 = no plaintext but basic parameter-store/env-var approach without rotation, Score 3 = managed secrets with rotation. Separate from the C24 rejection, which was about BLOCKER severity on SEC-Q5. Not a blocker for the ARA re-run.

- [ ] **C-7 — MOD surface-flag calibration for INF-Q2, SEC-Q2, and OPS questions (post-v4-scan).**
  The scanner showed INF-Q2 (managed databases) at 59% Score 1 and SEC-Q2 (encryption at rest) at 86% Score 1 across all portfolios — driven largely by OSS libraries and stateless utilities that have no database/data-at-rest surface at all. This is the MOD-side equivalent of the ARA R1/R6 recalibration. Libraries, stateless utilities, and CLIs with no persistent data should record these as "Not Evaluated (archetype-N/A)" rather than defaulting to Score 1. Scope: add surface-flag detection to MOD Step 1 (mirrors ARA Step 1.5) and apply calibration rows to INF-Q2, SEC-Q2, and selected OPS questions. Deferred per "don't touch MOD rubric now" — revisit after seeing the ARA v5 portfolio.

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
| 🔬 V3 calibration follow-ups | 5 | C-3, C-4, C-5, C-6 (MOD SEC-Q5), C-7 (MOD surface-flag) |
| ⚠️ Pre-flight | 3 | P0.1..P0.3 |
| 🤔 MOD scope decisions | 2 | G1, G2 |
| 🤖 ARA pre-flight | 2 | ARA-P0.1, ARA-P0.2 |
| 🔍 ARA-R Verification | 4 | V-R1..V-R4 (run zg-cmp 31-repo ARA v5) |
| 🔍 Verification | 6 | V1..V6 |
| 📦 Wrap-up | 3 | W1..W3 |
| **Total remaining** | **32** | |

**Next concrete step:** V-R1 — run `./run-assessments.sh` (ARA-only filter) for the 31 non-canary repos against the republished ARA TD `3g1ipe93e5d2wb6n5d4yqaf9`, then re-run `scan-rubric-quality.py` to confirm the severity distributions normalize.
