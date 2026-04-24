# Kiro Execution Plan — TD Edits Only

**Scope:** Two TDs. Ordered smallest → largest blast radius per assessment.
**Excluded:** Docx-only items, reply-only items, items blocked on reviewer confirmation, items requiring scope decisions (new questions, severity tier changes, scope reversals).
**Sources:** `quick-scripts/feedback-updates/kiro-feedback-changes.md`, `quick-scripts/feedback-updates/mod-feedback-analysis.md`, `quick-scripts/feedback-updates/ara-feedback-analysis.md`.
**Full analysis with rationale:** `kiro-feedback-todo.md` (keep for CR reference).

---

## Pre-flight (both TDs)

- [ ] Clean working tree, create branch `feedback/td-reviewer-pass`.
- [ ] Resolve B3 FIND uniqueness before edit: the "Archetype Calibration" string appears 4× in MOD TD. Use `#### INF-Q4:` header + preceding paragraph as anchor context.
- [ ] Resolve INF-Q2 Score 2 duplicate: WF-1 wording supersedes P2A-2 for the Score 2 row. Apply once, not twice.

---

# 🏗️ MOD Transformation Definition

`modernization-assessment/transformation_definition.md`

## Tier 1 — Terminology fixes (0 blast radius)

Trivial wording changes. Score semantics unchanged. Safe to apply first.

- [ ] **M1 — "compute tiers" → "compute resource types"** (INF-Q7 Score 4 rubric row; 1 hit).
- [ ] **M2 — "primary database" → "main production database"** in INF-Q8 Score 2 rubric row.
- [ ] **M3 — "primary database" → "main production database"** in INF-Q9 Score 3 rubric row.
- [ ] **M4 — "primary database" → "main production database"** in INF-Q2 Score 3 rubric row (WF-1 wording).

## Tier 2 — Discovery additions (rubric unchanged)

Look-for lists and question examples grow to match reality. Scoring unaffected.

- [ ] **M5 — Remove App Mesh** from discovery list (line 192) and INF-Q6 look-for (line 714). End-of-support Sept 30, 2026.
- [ ] **M6 — Add AppSync + IoT Core to INF-Q6** (question text + look-for).
- [ ] **M7 — Add `appspec.yml` (CodeDeploy) to CI/CD discovery** (file pattern list + INF-Q11 look-for).
- [ ] **M8 — Add MWAA to INF-Q3** workflow orchestration list (question text).
- [ ] **M9 — Add Amazon MQ to INF-Q4** (question text + look-for).
- [ ] **M10 — Add Neptune + Timestream to INF-Q2** (question text + look-for).
- [ ] **M11 — Add observability/DR resources to INF-Q10 look-for** — CloudWatch alarms, Route 53 health checks, Backup plans. Addresses Robert's reopened C10.

**Commit 1 (Tier 1 + 2):** `chore(mod-td): terminology fixes and missing AWS services (P2B, P3, analysis-C10)`

## Tier 3 — Scope + framing additions (non-rubric narrative)

One-line additions to Summary / why-it-matters. No rubric rows touched.

- [ ] **M12 — Add AWS scope statement** above `This assessment does NOT cover:` (Summary). Signals on-prem/multi-cloud excluded.
- [ ] **M13 — Name the 5 dimensions** on the `37 questions across 5 sections:` line (Summary). One-clause addition.
- [ ] **M14 — Remove misplaced DMS/SCT reference** from INF-Q2 why-it-matters. Belongs in pathway detail, not scoring rationale.
- [ ] **M15 — Add archetype-visibility note** above `**Archetype Calibration:**` in **INF-Q4 only** (not the other 3 occurrences). Makes the existing calibration visible to reviewers.
- [ ] **M16 — Clarify INF-Q11 covers both application and IaC pipelines** (question text).
- [ ] **M17 — Add S3 access-pattern sentence to DATA-Q1 why-it-matters.**
- [ ] **M18 — Add S3 File Gateway note to DATA-Q1 Score 2 rubric row.**
- [ ] **M19 — Broaden "containerize as-is" in APP-Q2 why-it-matters** → "containerize, migrate to serverless (Lambda), strangler fig extraction, or full decomposition."

**Commit 2 (Tier 3):** `docs(mod-td): clarify AWS scope, name dimensions, expand DATA-Q1 and APP-Q2 framing (P1C, P4)`

## Tier 4 — Rubric precision (score-row rewrites, same semantics)

Rubric rows rewritten for clearer score differentiation. Score direction unchanged — assessors using the old rubric land on the same score.

- [ ] **M20 — INF-Q1 Score 4** — "80%+ of compute" → service-count-based criterion ("≤1 EC2-based service remains").
- [ ] **M21 — INF-Q2 Score 2** — apply merged WF-1 wording (supersedes P2A-2).
- [ ] **M22 — INF-Q7 Scores 3 and 2** — custom vs default scaling policy sophistication.
- [ ] **M23 — APP-Q2 Scores 3 and 2** — schema separation + circular dependency signals.
- [ ] **M24 — APP-Q5 Scores 3 and 2** — define "inconsistent" as <50% adoption or conflicting schemes.
- [ ] **M25 — SEC-Q3 Scores 3 and 2** — auth method vs coverage differentiation.
- [ ] **M26 — SEC-Q3 Score 4** — carve-out for intentional public APIs.
- [ ] **M27 — SEC-Q5 Scores 3 and 2** — differentiate by what's in env vars (non-secret vs production credential).
- [ ] **M28 — SEC-Q7 Scores 2 and 1** — eliminate overlap. Score 2 = at least one tool; Score 1 = nothing.

**Commit 3 (Tier 4):** `refactor(mod-td): sharpen scoring rubric precision (P2A)`

## Tier 5 — Rubric edits addressing reviewer tone + reopens (moderate blast)

These change what a specific score *means* — not just wording. Verify against example reports after editing.

- [ ] **M29 — APP-Q1 tone fix.** Rewrite Score 1/2 rubric rows to attribute gaps to AWS tooling limits, not label the customer "not modern." Keep modernization framing (this is the counter to the rejected agent-framework reframe). Robert flagged P0.
  Example Score 1: `Languages with limited AWS SDK and cloud-native tooling (e.g., COBOL, VB6, Classic ASP) — requires custom integration or migration planning.`
- [ ] **M30 — SEC-Q2 Score 2/3 overlap.** Rework to differentiate on key type AND coverage, not coverage alone. Robert reopened.
- [ ] **M31 — INF-Q9 Score 2/3 multi-AZ wording.** Distinguish stateless-recoverable single-AZ compute from stateful single-AZ compute. Robert reopened.
- [ ] **M32 — SEC-Q2 Score 4 addition.** Extend to require centralized key management + rotation for customer-managed keys. Addresses Maia Thread 44.
- [ ] **M33 — DATA-Q3 Score 4 addition.** Add documented version-update procedure (downtime awareness, risk acknowledgment). Addresses Maia Thread 41.
- [ ] **M34 — INF-Q8 Score 4 extension.** Add cross-region backup replication as Score 4 signal. Addresses Maia Thread 29 (multi-region).
- [ ] **M35 — OPS-Q9 Score 4 + look-for.** Remove SCP as tagging recommendation. Replace with IaC enforcement + Tag Policies + AWS Config rules. SCPs reserved for security measures. Addresses Maia Thread 53.

**Commit 4 (Tier 5):** `refactor(mod-td): address reopened reviewer concerns + Herrera Soto pass (APP-Q1 tone, SEC-Q2, INF-Q9, DATA-Q3, INF-Q8, OPS-Q9)`

## Tier 6 — INF-Q7 full rework (coordinated multi-edit)

Do last. INF-Q7 gets touched in Tiers 1 + 4 already; this consolidates the broadening into a coherent edit.

- [ ] **M36 — INF-Q7 question broadening.** "auto-scaling mechanisms configured for compute workloads" → "...for compute, database, and other workloads."
- [ ] **M37 — INF-Q7 why-it-matters.** Add sentence covering DynamoDB auto-scaling, Aurora Serverless scaling.
- [ ] **M38 — INF-Q7 look-for.** Add DynamoDB auto-scaling, Aurora auto-scaling config to detection patterns.
- [ ] **M39 — INF-Q7 Score 3 and 2 rubric rewrite.** Expand beyond "primary compute" wording so rubric matches the broadened question. Without this, the rubric contradicts the question text.

**Commit 5 (Tier 6):** `refactor(mod-td): broaden INF-Q7 auto-scaling across compute + data (P4-3 four-part edit)`

---

# 🤖 ARA Transformation Definition

`agentic-readiness-assessment/transformation_definition.md`

Smaller set. ARA has tighter scope and fewer safe-to-ship items — everything controversial (MCP evaluation, severity changes) is excluded here.

## Tier 1 — Housekeeping (0 blast radius)

- [ ] **A1 — Remove App Mesh from ARA discovery** (line 282). Coordinate with MOD M5 — keeps both TDs consistent. End-of-support Sept 30, 2026.
- [ ] **A2 — Fix AUTH-Q4 duplicate "Look for" block.** Lines 702–727 have a copy-paste merge artifact with a garbled sentence between two identical "Look for" lists. Delete the duplicate; clean the garbled sentence.
- [ ] **A3 — Add "AgentCore Identity" to AUTH-Q1 look-for.** One detection-signal bullet. Doesn't change scoring.

**Commit 6 (ARA Tier 1):** `chore(ara-td): housekeeping — remove App Mesh, fix AUTH-Q4 duplicate, add AgentCore Identity signal`

## Tier 2 — Framing additions to Objective / Summary (non-rubric)

- [ ] **A4 — Dual-purpose framing in Objective.** Add one sentence naming the two use modes: portfolio-level telemetry AND use-case-level dependency checking for a specific agent workflow. RP endorsed.
- [ ] **A5 — Mention "remediation" in Summary.** One clause: findings include prioritized remediation guidance.
- [ ] **A6 — Design-time clarification in Summary or Objective.** One clause: "ARA is a design-time architecture review — evaluates whether controls exist in code and configuration, not whether they're effective at runtime."
- [ ] **A7 — Extend "does NOT cover" list** to include agent-level AI governance (model policy, prompt injection defense, safety evaluation). Names the boundary; does not invent integrations.
- [ ] **A8 — Control-layer note in Summary.** One sentence: controls may live at application, platform, or agent-architecture layer; ARA checks end-to-end presence. Addresses Riggs's architecture-responsibility question.

**Commit 7 (ARA Tier 2):** `docs(ara-td): dual-purpose framing, design-time clarification, governance boundary (C22, C24-C26, C30)`

## Tier 3 — Why-it-matters rewrites (one question at a time)

- [ ] **A9 — HITL dimension intro (Step 5).** Add one line clarifying ARA measures whether the system can *support* HITL, not whether HITL must be mandatory. Addresses C17.
- [ ] **A10 — AUTH-Q4 why-it-matters.** Adopt the "user is the subject, agent is the actor" semantic framing from Riggs C31. Same meaning, cleaner phrasing.
- [ ] **A11 — AUTH-Q4 why-it-matters (continued).** Add multitenancy cross-reference paragraph linking to DATA-Q2 and DATA-Q6. No severity change. Addresses Justin C11 without scope creep.
- [ ] **A12 — AUTH-Q2 why-it-matters.** Adopt scoped-permissions framing from Riggs C33 (drop the MCP reference from his proposed wording).
- [ ] **A13 — Step 2 (API dimension) intro.** Add one line: "When MCP-native integration is the target, findings here inform what an MCP server wrapping this system will need to expose." Acknowledges C12 without importing MCP rubrics.

**Commit 8 (ARA Tier 3):** `docs(ara-td): clarify AUTH and API framing, add multitenancy cross-reference (C11, C12, C17, C31, C33)`

---

# Verification (after all commits)

- [ ] **V1 — Grep stale terms in MOD TD:**
  - `compute tiers` → 0 hits
  - `App Mesh` → 0 hits
  - `Primary database` / `primary database` → 0 hits in rubric rows (audit any remaining)
- [ ] **V2 — Grep stale terms in ARA TD:**
  - `App Mesh` → 0 hits (after A1)
  - AUTH-Q4 has exactly one "Look for" block (after A2)
- [ ] **V3 — Spot-check affected rubrics** for coherent 1→4 progression:
  - MOD: INF-Q1, INF-Q2, INF-Q7, INF-Q9, APP-Q1, APP-Q2, APP-Q5, SEC-Q2, SEC-Q3, SEC-Q5, SEC-Q7, OPS-Q9
  - ARA: no rubric scores changed — skip.
- [ ] **V4 — Cross-check portfolio TDs.** `portfolio-modernization/transformation_definition.md` references question IDs only; no rubric text share. Confirm no drift.
- [ ] **V5 — Example reports sanity check.** Spot-read `example-reports/v2-full-assessment/modernization-assessment/*.md`. If any scores would shift, note in CR as stale (don't regenerate unless asked).
- [ ] **V6 — Question count unchanged.** MOD = 37. ARA = 43. Neither changes in this plan.

---

# Commit Strategy

| # | TD | Commit message |
|---|----|----------------|
| 1 | MOD | `chore(mod-td): terminology fixes and missing AWS services (P2B, P3, analysis-C10)` |
| 2 | MOD | `docs(mod-td): clarify AWS scope, name dimensions, expand DATA-Q1 and APP-Q2 framing (P1C, P4)` |
| 3 | MOD | `refactor(mod-td): sharpen scoring rubric precision (P2A)` |
| 4 | MOD | `refactor(mod-td): address reopened reviewer concerns + Herrera Soto pass` |
| 5 | MOD | `refactor(mod-td): broaden INF-Q7 auto-scaling across compute + data (P4-3)` |
| 6 | ARA | `chore(ara-td): housekeeping — App Mesh, AUTH-Q4 cleanup, AgentCore Identity signal` |
| 7 | ARA | `docs(ara-td): dual-purpose framing, design-time clarification, governance boundary` |
| 8 | ARA | `docs(ara-td): clarify AUTH and API framing, add multitenancy cross-reference` |

Land 1–3 first (low-risk). 4–5 next (reviewer reopens). 6–8 can go in a separate CR if MOD pass is large.

---

# Excluded from this plan (intentional)

These are tracked in `kiro-feedback-todo.md` but not here because they need decisions, reviewer confirmation, or live in the docx:

- MOD R1/R2/R3/R4/R5 rejections (counter-proposals, not edits)
- MOD Phase G (new questions — IaC governance, ops coverage, SEC-Q5 rework) — scope decision required
- MOD N8 (SEC-Q5 Score 1/4 rework) — pending Maia confirmation
- ARA MCP evaluation (C12/C14/C15 escalation) — scope reversal requires leadership decision
- ARA severity tier changes (C11/C32 escalation proposals) — breaks readiness profile math
- All docx-only items (WAR → WAFR, Programs table, Customer Positioning, intro narrative)
- All reply-only items (respond in reviewer threads, no file changes)

Anything on this list lands *after* this plan ships, or not at all.
