# TODO — Open Work

Only items that are still **open and actionable** live here. Everything shipped, rejected, reply-only, or deferred is in `kiro-feedback-archive.md` for CR and reviewer traceability.

**Last verified:** Apr 29, 2026 — every item below was grep'd against the live TDs. Confirmed NOT YET shipped.

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

Surfaced by the v2-vs-v3 comparison. Keep in mind for the next TD iteration or assessment run.

- [x] **C-1 — APP-Q1 two-axis rubric (language + framework + SDK).** ✅ Shipped Apr 30, 2026.
  Rewrote APP-Q1 with a two-axis calibration: (a) language/runtime modernity, (b) framework/SDK modernity. Score 4 = all modern (Python 3.10+, Java 17+ with Spring Boot 3.x and AWS SDK v2, modern .NET 6-10 with AWS SDK v3). Score 3 = modern language with framework or SDK lag (Java 17 + Spring Boot 2.7; modern .NET with SDK v2 partial adoption). Score 2 = compound regression across all three axes (Java 8 + Spring Boot 2.x + SDK v1; .NET Framework 4.x + legacy ASP.NET + SDK v2 or older; also PHP/Ruby/Perl). Score 1 = no meaningful AWS SDK (COBOL, VB6). The scanner data confirmed .NET Framework 4.8 (greenshot) and modern .NET (Sonarr, cartservice) were being conflated at Score 3, and Java 8 alone was scoring 4 in some reports — the new rubric separates these cleanly.

- [x] **C-2 — Lift ARA framing into per-question why-it-matters.** ✅ Shipped Apr 30, 2026.
  Added dual-purpose framing to AUTH-Q4 why-it-matters (portfolio telemetry vs use-case-level dependency checking). Added design-time + control-layer framing to AUTH-Q1 why-it-matters (machine identity sits at the control layer; weak attribution invalidates downstream AUTH-Q2/Q3/Q6). Added HITL-support-not-mandatory framing to HITL-Q1 why-it-matters. These clauses were already present in the Summary/Objective but did not render in report output because reports quote per-question text, not Summary.

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

## ✅ MOD TD — Remaining Clean Wins

Items verified not yet shipped. FIND/REPLACE text lives in `quick-scripts/feedback-updates/kiro-feedback-changes.md`.

### Scoring rubric precision

- [x] **B3 — Extend archetype-visibility Note to INF-Q3, APP-Q3, APP-Q4.** ✅ Shipped Apr 30, 2026.
  Added the `> **Note:** This question uses archetype-sensitive calibration...` block above `**Archetype Calibration:**` in INF-Q3, APP-Q3, and APP-Q4 so assessors see archetype sensitivity consistently across all 4 archetype-sensitive questions.

### Net-new additions

- [x] **F5 — INF-Q11 ↔ SEC-Q7 cross-reference.** ✅ Shipped Apr 30, 2026.
  Added one sentence to INF-Q11 why-it-matters noting CI/CD automation alone is not sufficient — pipelines must also include security validation (SAST, DAST, dependency scanning). Cross-references SEC-Q7 for the pipeline-security evaluation.

- [x] **F6 — INF-Q7 Score 4: business-metric-driven scaling.** ✅ Shipped Apr 30, 2026.
  Extended Score 4 to call out business-metric-driven scaling (custom CloudWatch metrics on requests-in-flight, orders-per-second, queue depth) as the maturity signal where purely technical metrics are insufficient.

**Commit F:** `feat(mod-td): archetype-visibility notes (B3) and INF-Q7/INF-Q11 enhancements (F5, F6)` — pending squash-commit.

### Phase G — Scope decisions (pending P0.3)

- [ ] **G1 — IaC governance as a new INF question** (Thread 32 / N5).
  Scope change: affects question count (11→12 INF), category score math, N/A mappings. Settle via P0.3 before execution.

- [ ] **G2 — Operations gaps — load testing, chaos, synthetics, metrics definition** (Thread 51 / N6).
  Options: (a) new OPS question covering resilience testing, (b) extensions across OPS-Q3/Q4/Q7 rubrics, (c) defer to future TD version. Settle via P0.3.

> **G3 — SEC-Q5 rework is already shipped.** INF-Q5 Score 4 references PrivateLink, VPC Lattice, IPAM, zero-trust; Score 1 references default VPC. No action.

**Commit G (if adopted):** `feat(mod-td): add IaC governance question and resilience testing coverage (G1-G2)`

---

## 🤖 ARA TD — Remaining Items

All Part A (A1, A3, A4, A5, A7) shipped. Parts B1/B2/B3/B4 shipped. A2 shipped (subject/actor phrasing landed in AUTH-Q4). A6 shipped (AI governance carve-out in scope exclusion). A8 shipped (AUTH-Q4 duplicated Look-for block cleaned up).

**No remaining ARA TD edits from the original reviewer pass.** All Part A and Part B items are in the live TD as of Apr 29, 2026.

> See the new **ARA TD — Rubric Recalibration** section below for a larger open tranche surfaced by the zg-cmp 34-repo run (Apr 29, 2026).

### ARA Pre-flight (if reopened)

- [ ] **ARA-P0.1 — Reconcile question numbering.** Analysis doc says "AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User" — actual TD has this at AUTH-Q4. Map both in CR description when replying to C11/C31.
- [ ] **ARA-P0.2 — Retrieve docx anchors for C9 and C13.** Both need comment-position lookup before response.

---

## 🎯 ARA TD — Rubric Recalibration (from zg-cmp v4 portfolio run)

**Source:** `analyze-ara-patterns.py` run across all 34 zg-cmp ARA reports (Apr 29, 2026).

**Problem:** 26 of 43 questions show ≥85% concentration on one severity — meaning the question isn't differentiating between repos. 11 non-data-handling OSS tools (tqdm, webpack, gulpjs, serverless, getlift, motdotla-node-lambda, aws-sdk-mock, openapi-generator, greenshot, 3 Angular templates) all get the same BLOCKER/RISK-SAFETY findings as hapi-fhir (a healthcare library that actually processes PHI). The rubric doesn't distinguish between "no PII controls because this is a progress bar" and "no PII controls on a PHI-handling system."

### Root causes

1. **N/A mapping is too coarse** — filters only on `repo_type` (library / infra-only / deployment-config / monorepo). Many build tools / scaffolds / browser SDKs classify as `application` and fall through to "all 43 questions apply."
2. **Archetype calibration only exists on 4/43 questions** (AUTH-Q4, STATE-Q5, STATE-Q6, DATA-Q5). The other 39 don't calibrate — so `stateless-utility` repos get dinged on DATA-Q1, DATA-Q6, AUTH-Q6, etc.
3. **No "target-system-has-this-surface?" scope gate** before scoring. TD jumps straight to "is X classified/rate-limited/redacted?" without first asking "does this system have data/an API/logs?"
4. **Conditional downgrades produce identical findings across repos.** AUTH-Q6 resolves to RISK-SAFETY 100% of the time when `agent_scope: read-only` — finding text is identical whether the repo is hapi-fhir or tqdm.

### The data (severity concentration across 34 repos)

| Question | % on dominant severity | Assessment |
|---|---|---|
| **DATA-Q1** | 88% BLOCKER | Broken — flags build tools for "no PII classification" |
| **DATA-Q2, DATA-Q6** | 91–94% RISK-SAFETY | Same pattern — non-data repos dinged |
| **STATE-Q1, STATE-Q5** | 91% RISK-SAFETY | Stateless utilities flagged for "no rate limiting" |
| **AUTH-Q6** | 100% RISK-SAFETY | Conditional→RISK collapse, zero differentiation |
| **AUTH-Q2, AUTH-Q3, AUTH-Q7** | 88–94% RISK-SAFETY | Libraries flagged for "no authorization surface" |
| **DISC-Q1** | 100% RISK-QUALITY | Every OSS repo dinged for no schema versioning CI |
| **OBS-Q1, OBS-Q2** | 94–97% RISK-QUALITY | Libraries don't own tracing/dashboards — their consumers do |
| **ENG-Q1, Q2, Q3** | 85–97% RISK-QUALITY | Same issue — consumer-facing ops concerns applied to libs |
| **API-Q2, API-Q3** | 91–94% RISK-QUALITY | Repos with no HTTP surface still getting API-quality findings |
| **HITL-Q3** | 97% RISK-QUALITY | "No sandbox/staging" applied to libraries |

### Items (ordered by impact)

> **All 9 items shipped Apr 29, 2026 on branch `fix/ara-calibration`. Commits `cf58756`, `044c369`, `3826b58`, `ed9eca6`, `dd35bce`.** Pending verification (V-R1 through V-R4 below) — re-run zg-cmp portfolio to confirm the calibration produces the expected severity distribution.

- [x] **ARA-R1 — DATA-Q1 scope gate + archetype calibration. HIGHEST PRIORITY.** Shipped in `044c369`.
  Rewritten with Stage A (does this system handle sensitive data?) / Stage B (classification check) structure. `stateless-utility` archetype and `dev-library-application` override land on INFO. Expected portfolio impact pending V-R1.

- [x] **ARA-R2 — DATA-Q2, DATA-Q6 archetype + scope calibration.** Shipped in `3826b58`.
  Both questions now downgrade to INFO when the system has no persistent data store and no user-data logging, or for `stateless-utility` archetype. Conditional BLOCKER logic on DATA-Q2 preserved.

- [x] **ARA-R3 — STATE-Q1, STATE-Q5 archetype calibration.** Shipped in `3826b58`.
  STATE-Q1 downgrades to INFO when no write operations and no HTTP/RPC surface. STATE-Q5 downgrades to INFO when no HTTP/RPC surface. Both also honor the dev-library-application override.

- [x] **ARA-R4 — OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3 library-aware calibration.** Shipped in `ed9eca6`.
  All five downgrade to INFO for `dev-library-application` or when no HTTP/RPC surface (and, for ENG-Q1, also no auth surface). Libraries that ship instrumentation hooks satisfy the concern without owning the tracing/alerting/rollback infrastructure.

- [x] **ARA-R5 — API-Q2, API-Q3 scope gate for "no HTTP surface".** Shipped in `3826b58`.
  Both downgrade to INFO when `has_http_rpc_surface` is false or for `dev-library-application`.

- [x] **ARA-R6 — Add a "target-system-surface" detection step.** Shipped in `cf58756`.
  New Step 1.5 records five surface flags (has_persistent_data_store, has_http_rpc_surface, has_auth_surface, has_write_operations, has_logging_of_user_data). Feeds all downstream scope gates. Renumbered archetype detection to Step 1.6.

- [x] **ARA-R7 — Rewrite AUTH-Q6 and AUTH-Q7 rubric+finding to differentiate when downgraded.** Shipped in `dd35bce`.
  Both downgrade to INFO for `dev-library-application` or when no auth surface (+ no write operations for AUTH-Q6). Conditional BLOCKER logic on AUTH-Q6 preserved.

- [x] **ARA-R8 — Dev-library-application archetype override (option b).** Shipped in `cf58756` as part of Step 1.5.
  When archetype is `stateless-utility` AND 3+ surface flags are `false`, apply the `library` N/A mapping as the scoring baseline. ARA-TD-internal, no Power or portfolio config changes needed. Option (b) chosen per D1 decision.

- [x] **ARA-R9 — HITL-Q3 library calibration.** Shipped in `3826b58`.
  Downgrades to INFO for `dev-library-application` or when no HTTP/RPC surface and no data store.

### Sequencing

1. **R6 first** (target-system-surface detection) — structural foundation that R1–R5 depend on
2. **R1** (DATA-Q1) — highest-impact single change, and the simplest to ship if R6 is in place
3. **R2, R3, R5** (calibration extensions) — apply the same pattern to siblings
4. **R4, R9** (library-aware OBS/ENG/HITL calibration)
5. **R7** (AUTH-Q6/Q7 differentiation) — independent of the others, can ship anytime
6. **R8** (new repo_type) — open scope question, resolve before or alongside R6

### Commit Strategy

| Commit | Scope | Message | Status |
|--------|-------|---------|--------|
| `cf58756` | R6 + R8 | `feat(ara-td): add target-system-surface detection in Step 1 for finer N/A mapping` | ✅ landed |
| `044c369` | R1 | `refactor(ara-td): add scope gate + archetype calibration to DATA-Q1` | ✅ landed |
| `3826b58` | R2, R3, R5, R9 | `refactor(ara-td): extend surface-flag calibration to DATA-Q2/Q6, STATE-Q1/Q5, API-Q2/Q3, HITL-Q3` | ✅ landed |
| `ed9eca6` | R4 | `refactor(ara-td): library-aware calibration for OBS-Q1/Q2 and ENG-Q1/Q2/Q3` | ✅ landed |
| `dd35bce` | R7 | `refactor(ara-td): differentiate AUTH-Q6/Q7 findings when conditional downgrades` | ✅ landed |

### Verification (post-edit)

- [ ] **V-R1 — Re-run zg-cmp portfolio** with recalibrated TD. Expected: DATA-Q1 BLOCKER count drops from 30 → under 10. AUTH-Q6 and DATA-Q2 RISK-SAFETY drop from 31–34 → single digits for non-data repos.
- [ ] **V-R2 — Spot-check hapi-fhir.** Must still score BLOCKER on DATA-Q1 (PHI-handling) and keep RISK-SAFETY on DATA-Q2/Q6. Recalibration must not under-flag real PII systems.
- [ ] **V-R3 — Spot-check Graylog2 + umami** (observability/analytics repos that do handle user data). Must keep RISK-SAFETY on DATA-Q6 — they absolutely can leak PII into logs.
- [ ] **V-R4 — Verify portfolio ARA trigger logic** isn't affected. Check `portfolio-agentic-readiness/transformation_definition.md` doesn't reference rubric text verbatim.

### Risk Notes

- **Under-flagging is the main risk.** The goal is to remove false positives on tools/libraries, NOT to downgrade real data-handling systems. V-R2 and V-R3 exist specifically to catch that regression.
- **R8 scope question.** Adding `dev-library-application` is a taxonomy change. Option (b) in R8 (archetype overrides repo_type) is less invasive — may be preferable.
- **Example reports will drift.** v3 reports showed the over-strict patterns as "working" findings. After R1-R7 land, many of those will change severity. Flag as expected drift in the CR, don't regenerate unless asked.

---

## 🔍 Verification (pre-CR)

- [ ] **V1 — Grep stale terms after edits land:**
  - `compute tiers` — 0 hits required (already clean)
  - `App Mesh` — 0 hits in MOD and ARA TDs (both already clean)
  - `primary database` / `Primary database` — 0 expected hits (B2 shipped)
  - `in IaC` — unchanged (R2 rejected, stays IaC)
- [ ] **V2 — Spot-check reworked rubrics** (INF-Q3, APP-Q3, APP-Q4 after B3; INF-Q7 after F6; INF-Q11 after F5) for coherent 1→4 progression.
- [ ] **V3 — Cross-check portfolio TD.** `portfolio-modernization/transformation_definition.md` references question IDs only. Re-verify no rubric text drift.
- [ ] **V4 — Cross-check example reports.** `example-reports/v2-full-assessment/modernization-assessment/*.md` — flag as stale in CR if any scores shift.
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
- **INF-Q7 edit chain** — R3-rework is already shipped (compute+data covered). Only F6 remains; apply carefully without reintroducing compute-only wording.
- **Phase G changes question count** — update Summary counter, category math, N/A mappings before shipping.
- **JSON schema stability (Phase H)** — once external tooling depends on it, breaking changes bump schema version.
- **Part 3 scope discipline** — if pressed to include docx-only items in TD CR, hold the line.

---

## What's left, at a glance

| Category | Count | Items |
|----------|-------|-------|
| 🚀 Phase H JSON | 7 | H-1..H-7 |
| 🔄 GF replies | 2 | GF-1, GF-2 |
| 🔬 V3 calibration follow-ups | 5 | C-3, C-4, C-5, **C-6 (MOD SEC-Q5)**, **C-7 (MOD surface-flag)** |
| 🎯 **ARA rubric recalibration** | 9 | **R1..R9 all shipped on `fix/ara-calibration` (Apr 29, 2026) — pending V-R1..V-R4 portfolio re-run** |
| ⚠️ Pre-flight | 3 | P0.1..P0.3 |
| ✅ MOD edits | 0 | **B3, F5, F6 shipped Apr 30** |
| 🤔 MOD scope decisions | 2 | G1, G2 |
| 🤖 ARA edits (original pass) | 0 | All shipped |
| 🔍 Verification | 6 | V1..V6 |
| 🔍 ARA-R Verification | 4 | V-R1..V-R4 (run zg-cmp portfolio against recalibrated TD) |
| 📦 Wrap-up | 3 | W1..W3 |
| **Total remaining** | **32** | |

Of those 32, **C-1 and C-2 shipped Apr 30** — next concrete step is republishing both TDs and re-running ARA for the 31 non-canary repos to verify V-R1..V-R4.
