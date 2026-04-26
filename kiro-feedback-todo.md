# TODO — Reviewer Feedback Pass on MOD Transformation Definition

**TD target:** `modernization-assessment/transformation_definition.md` (1712 lines)
**Source of FIND/REPLACE:** `quick-scripts/feedback-updates/kiro-feedback-changes.md`
**Source of reviewer context:** `quick-scripts/feedback-mod-action.md`
**Latest reviewer state (Apr 24):** `quick-scripts/feedback-updates/mod-feedback-analysis.md` — 37 threads, 59 comments. Maia Herrera Soto and Robert Hanuschke reopens noted. Angel, Javier made untracked content edits on Apr 24 (review before executing).

> **Note:** This TODO tracks only changes to the **transformation_definition.md**. Reviewer items targeting the companion docx (intro framing, Programs table, Customer Positioning, Appendix narratives) are listed separately under "📄 Docx-only" for visibility and handled in the docx review pass, not here.

---

## ✔️ Validation Report (checked against live TDs)

**FIND strings verified present and unique** for all `kiro-feedback-changes.md` tasks:
- A1, A2, B1, B4–B9, C1, C2, D1–D6, E3, E5, WF-1 leftovers ✅
- **B3 caveat:** "Archetype Calibration" line appears 4× in TD (INF-Q3, INF-Q4, APP-Q3, APP-Q4). The FIND in `kiro-feedback-changes.md` isn't unique — P2A-3 needs more surrounding context to target INF-Q4 specifically. Fix before executing.

**Pathway trigger impact check:**
- B9 (SEC-Q7 Score 2/1 semantic shift): SEC-Q7 is not a pathway trigger. Safe.
- R3 / B4 (INF-Q7 changes): INF-Q7 is not a pathway trigger. Safe.
- B12 (SEC-Q2 changes): Not a pathway trigger. Safe.
- B13 (INF-Q9 changes): Not a pathway trigger. Safe.
- B14 (INF-Q10 look-for expansion): INF-Q10 < 3 triggers *Move to Modern DevOps*. Look-for text doesn't change scoring. Safe.

**Cross-TD impact:**
- Portfolio MOD TD references question IDs only, not rubric text. **V5 is low risk.**
- Bridge TD has no shared rubric text. Safe.
- ⚠️ **ARA TD also mentions App Mesh** (`agentic-readiness-assessment/transformation_definition.md` line 282). D1 removes it from MOD only. Consider extending D1 to also patch ARA to stay consistent — or leave as deliberate scope split.

**Example report impact:**
- "primary database" appears in 2 online-boutique reports (finding/recommendation text, not rubric quotes). C2 rename causes mild staleness. Don't regenerate unless asked.
- No rubric text (e.g., "80%+ of compute", "compute tiers", "Most secrets managed") is quoted verbatim in example reports. **V6 is low risk.**

**N1 target confirmed:** SCP reference lives in OPS-Q9 resource tagging (Score 4 rubric row + look-for line). Confirmed via grep in live TD.

---

## ⚠️ Pre-flight

- [ ] **P0.1 — Clean working tree.** `git status` clean, then `git checkout -b feedback/mod-td-reviewer-pass`.
- [ ] **P0.2 — Read the TD once end-to-end** for orientation before any edits.
- [ ] **P0.3 — Fix B3 FIND uniqueness.** P2A-3's FIND must include enough context to target INF-Q4's Archetype Calibration line only (not INF-Q3, APP-Q3, or APP-Q4). Use the preceding `#### INF-Q4:` header + the paragraph above as anchor context.
- [ ] **P0.4 — Resolve INF-Q2 Score 2 duplicate.** Both P2A-2 and WF-1 rewrite the same row. WF-1's wording ("Main production databases…") is preferred. Apply WF-1 instead of P2A-2 for that specific row. Keep P2A-2 where it doesn't overlap.
- [ ] **P0.5 — Decide on multi-region scope.** Multi-region topic (Thread 29 / analysis-C13) could land in INF-Q8 (backups) or INF-Q9 (HA/fault isolation) or become a new question. Decide before Phase F.
- [ ] **P0.6 — Diff latest docx against TD.** Angel, Javier edited the docx Apr 24 with no comments — confirm no silent TD-relevant changes were made. Also confirm Maia's C27 ("Made it a bit more agnostic" Apr 24) about API Gateway language is reflected in the TD, not just the docx.
- [ ] **P0.7 — Decide D1 scope: MOD only vs MOD + ARA.** App Mesh is referenced in both TDs. Recommend extending D1 to patch ARA line 282 for consistency, or explicitly scope D1 as MOD-only.
- [ ] **P0.8 — Decide N5 and N6 scope.** Both propose **new TD questions** (IaC governance as a new INF question; ops gaps — chaos, load, synthetics — as a new OPS question or extensions). New questions change total count (37 → 38/39) and ripple into N/A mappings and category score math. Settle before Phase F.

---

## ✅ Part 1 — TD Clean wins (adopt as specified in `kiro-feedback-changes.md`)

All items below change the **transformation_definition.md** only. FIND/REPLACE text lives in `kiro-feedback-changes.md`.

### Phase A — TD Scope + structural (Summary / Objective)

- [ ] **A1 — P1C-1: Add AWS scope statement.** Prepend AWS-targeting paragraph above `This assessment does NOT cover:` in Summary. Addresses C5 (Turrini), Thread 4.
- [ ] **A2 — P4-1: Name the 5 dimensions on the `37 questions across 5 sections:` line.** One-line addition to Summary. Addresses C3 (Omran).

### Phase B — TD Scoring rubric precision (P2-A + reopens)

- [ ] **B1 — P2A-1: INF-Q1 Score 4** — service-count-based criterion.
- [ ] **B2 — INF-Q2 Scores 2 and 3** — apply WF-1 wording per P0.4 (supersedes P2A-2 for Score 2).
- [ ] **B3 — P2A-3: INF-Q4** — prepend archetype-visibility note above `**Archetype Calibration:**`.
- [ ] **B4 — P2A-4: INF-Q7 Scores 3 and 2** — custom vs default scaling policies.
- [ ] **B5 — P2A-5: APP-Q2 Scores 3 and 2** — schema separation + circular deps.
- [ ] **B6 — P2A-6: APP-Q5 Scores 3 and 2** — define "inconsistent" (most-follow vs <50%).
- [ ] **B7 — P2A-7: SEC-Q3 Scores 3 and 2** — auth method vs coverage.
- [ ] **B8 — P2A-8: SEC-Q5 Scores 3 and 2** — what's in env vars.
- [ ] **B9 — P2A-9: SEC-Q7 Scores 2 and 1** — eliminate overlap with Score 1.
- [ ] **B10 — WF-3: SEC-Q3 Score 4** — carve-out for intentional public APIs.
- [ ] **B11 — analysis-C12: APP-Q1 tone fix.**
  Flagged P0 by Robert — calling customer environments "not modern" for language choice sounds judgmental. Separate from R1's rejected reframe — keep modernization framing, rewrite Score 1/2 wording to attribute the gap to AWS tooling limits, not to the customer.
  Example Score 1: `Languages with limited AWS SDK and cloud-native tooling (e.g., COBOL, VB6, Classic ASP) — requires custom integration or migration planning.`
- [ ] **B12 — analysis-C23 (Robert reopened): SEC-Q2 Score 2/3 overlap.**
  Current rubric makes "some KMS" worse than "AWS-managed everywhere." Rework Score 2/3 to differentiate on key type AND coverage, not coverage alone.
- [ ] **B13 — analysis-C15 (Robert): INF-Q9 multi-AZ wording.**
  Current rubric treats single-AZ compute as a hard Score 1/2. A stateless service with fast ASG replacement across AZs can be resilient without persistent dual-AZ compute. Rework Score 2/3 to distinguish stateless-recoverable single-AZ from stateful single-AZ.
- [ ] **B14 — analysis-C10 (Robert reopened): INF-Q10 look-for scope.**
  Expand look-for text beyond the 4 resource categories (compute / networking / databases / messaging) to include observability and DR resources (CloudWatch alarms, Route 53 health checks, Backup plans).

**Commit A:** `refactor(mod-td): sharpen scoring rubrics, fix APP-Q1 tone, resolve reopened rubrics (P1C, P2A, P4-1, analysis-C10/C12/C15/C23)`

### Phase C — TD Terminology fixes (P2-B)

- [ ] **C1 — Task 7: "compute tiers" → "compute resource types"** (INF-Q7 Score 4 rubric row).
- [ ] **C2 — WF-1 leftovers: remaining "primary database" → "main production database"**
  - [ ] INF-Q8 Score 2 rubric row
  - [ ] INF-Q9 Score 3 rubric row

### Phase D — TD Missing AWS services (P3)

- [ ] **D1 — Task 1: Remove App Mesh references.** End-of-support Sept 30, 2026. Two hits: discovery list (line 192) and INF-Q6 look-for (line 714). See P0.7 for ARA-TD extension decision.
- [ ] **D2 — Task 2: Add AppSync + IoT Core to INF-Q6** (question + look-for).
- [ ] **D3 — Task 3: Add `appspec.yml` (CodeDeploy) to CI/CD discovery** (two hits).
- [ ] **D4 — Task 4: Add MWAA to INF-Q3** workflow orchestration list.
- [ ] **D5 — Task 5: Add Amazon MQ to INF-Q4** (question + look-for).
- [ ] **D6 — Task 6: Add Neptune + Timestream to INF-Q2** (question + look-for).

**Commit B:** `feat(mod-td): add missing AWS services and clarify terminology (P2B, P3)`

### Phase E — TD Content enhancements (P4 + wording fixes)

- [ ] **E1 — P4-2: Add S3 access-pattern assessment to DATA-Q1.** Addresses C6 / Thread 5.
- [ ] **E2 — P4-4: Highlight Amazon S3 File Gateway in DATA-Q1 Score 2 note.** Addresses C26.
- [ ] **E3 — P4-5: Remove misplaced DMS/SCT reference from INF-Q2 why-it-matters.** Addresses C34.
- [ ] **E4 — P4-6: Clarify INF-Q11 covers application AND IaC pipelines.** Addresses C37.
- [ ] **E5 — WF-2: Broaden "containerize as-is" to include serverless.** Replacement wording is "containerize, migrate to serverless (Lambda), strangler fig extraction, or full decomposition" — clean list extension in APP-Q2 why-it-matters.

**Commit C:** `docs(mod-td): expand DATA-Q1 coverage, broaden modernization strategies (P4, WF)`

### Phase F — TD Net-new additions (from `feedback-mod-action.md`)

All items below are rubric or look-for extensions, not scope shifts. Each targets a specific TD rubric row.

- [ ] **F1 — Thread 53: Replace SCPs recommendation for tagging in OPS-Q9.**
  Rewrite Score 4 rubric row and look-for. SCPs are the wrong tool for tag enforcement — hit char limits, per-service action variance. Recommendation: IaC enforcement, Tag Policies, AWS Config rules. SCPs reserved for security measures.
- [ ] **F2 — Thread 29: Add multi-region to INF-Q8 or INF-Q9.**
  Per P0.5 decision. Extend INF-Q8 Score 4 to require cross-region backup replication, OR extend INF-Q9 rubric to include multi-region data durability as Score 4.
- [ ] **F3 — Thread 41: Add versioning-update process to DATA-Q3 Score 4.**
  Engine version pinning is not enough. Extend Score 4 to require documented update procedure (downtime awareness, risk acknowledgment).
- [ ] **F4 — Thread 44: Add key management + rotation to SEC-Q2.**
  Extend Score 4 to include centralized key management + rotation when customer-managed keys are used. Coordinate with B12 so the rubric rewrite lands once.
- [ ] **F5 — Thread 35 (N9): Cross-reference SEC-Q7 from INF-Q11.**
  Add one sentence to INF-Q11 why-it-matters noting that CI/CD automation alone is not enough — pipelines must include security validation (→ SEC-Q7). Coordinate with E4.
- [ ] **F6 — Thread 22 (N10): Business-metric-driven scaling in INF-Q7 Score 4.**
  If R3 is reworked and applied (INF-Q7 broadening), extend Score 4 to mention business-metric-based scaling as the maturity signal. Depends on R3 rework decision.

**Commit F:** `feat(mod-td): incorporate Herrera Soto pass — tagging, multi-region, key management, versioning, pipeline security (F1–F6)`

### Phase G — TD Scope decisions (pending)

- [ ] **G1 — Thread 32 / N5: IaC governance as a new INF question.**
  Lucas's reply in-thread agrees this is a valid concern. Deciding to add a new question is a scope change — affects question count (11→12 INF questions), category score math, N/A mappings. Settle via P0.8 before execution.
- [ ] **G2 — Thread 51 / N6: Operations gaps — load testing, chaos engineering, synthetic monitoring, metrics definition.**
  Options: (a) single new OPS question covering resilience testing, (b) extensions across OPS-Q3/Q4/Q7 rubrics, (c) defer to a future TD version. Settle via P0.8.
- [ ] **G3 — Thread 16 / N8: SEC-Q5 Score 1 + Score 4 rework.**
  Lucas proposed Score 1 as "deployed in default VPC with public config." Score 4 extended to include PrivateLink, VPC Lattice, CloudWAN, zero-trust. **Blocked on Maia's confirmation.** Apply once confirmed; otherwise defer.

**Commit G (if adopted):** `feat(mod-td): add IaC governance question and resilience testing coverage (G1–G3)`

---

## ❌ Part 2 — TD Reject (scope mismatch; keep rubric model intact)

- [ ] **R1 — Task 10 (P1-B): Reframe APP-Q1 from "language modernity" to "SDK + agent framework coverage."**
  **Reject as written.** The replacement collapses language maturity into agent-framework availability — an ARA concern, not MOD. Also loses the legitimate "legacy language → modernization blocker" signal (COBOL/VB6/Classic ASP).
  **Counter-proposal:** B11 fixes the tone without the reframe. If SDK/agent coverage needs capturing, add a new question (APP-Q7) or move to ARA.

- [ ] **R2 — Task 9: "in IaC" → "in Terraform/CloudFormation" (two lines).**
  **Reject.** TD uses "IaC" as the superset in ~6 other places and discovery includes CDK, Helm, Kustomize, Ansible. Narrowing two instances excludes CDK (AWS-native) and creates cross-TD inconsistency.
  **Counter-proposal:** Drop the task. Current wording is consistent.

- [ ] **R3 — Task P4-3: Broaden INF-Q7 beyond compute auto-scaling (3-part edit).**
  **Needs rework, not straight reject.** The proposed question + why-it-matters + look-for edits are fine, but rubric rows still say "compute tiers" and "primary compute." After C1 renames "compute tiers" to "compute resource types," Score 3 and 2 still read as compute-only. Fuzzy scoring results.
  **Counter-proposal:** Apply P4-3 as a 4-part edit — add a rubric rewrite that expands Score criteria to cover compute AND data/managed-service auto-scaling. Coordinate with F6.

- [ ] **R4 — analysis-C24 (Robert + Maia): "Plaintext credentials = security blocker, not low score."**
  **Reject — scope mismatch with MOD's scoring model.** MOD uses 1–4 numeric scoring. BLOCKER/RISK/INFO severity is an ARA construct. Importing it into MOD would break overall/category score math, pathway triggers, and N/A handling (all assume numeric scores).
  **Counter-proposal:** Keep SEC-Q5 = 1 for plaintext credentials in MOD, but strengthen the **recommendation text** in the Report Template to flag "address before any modernization work" — deliver the severity signal through recommendation copy, not score type.

- [ ] **R5 — analysis-C21 (Robert): "CloudTrail belongs in WAFR, not modernization."**
  **Reject — intentional overlap.** CloudTrail presence is a prerequisite for any auditable modernization work. Lucas already replied with this reasoning in-thread. No TD edit.
  **Counter-proposal:** Close thread with Lucas's existing reply. Keep SEC-Q1 as-is.

---

## 📄 Docx-only items (NOT TD work — track in docx review pass)

These reviewer comments target the companion docx (`modernization-readiness-assessment-v2.docx`) — intro framing, Customer Positioning, Programs tables, Appendix narratives. They do **not** belong in the TD edit cycle.

| Analysis ID | Topic | Docx location |
|-------------|-------|---------------|
| C22 | "WAR" → "WAFR" abbreviation | Scope Boundary narrative (kiro-feedback-changes.md Task 8 already calls out "docx only") |
| C6 | "Assessment vs questionnaire" framing | Intro / opening narrative |
| N7 / Thread 2 | Cross-validate with Cloud Maturity Assessment 3.0 | Intro or Appendix — relationship with other AWS assessments |

---

## 💬 Reply-only items (neither TD nor docx edits — respond in reviewer thread)

| Analysis ID | Topic | Suggested response |
|-------------|-------|--------------------|
| C5 (Gianfranco) | Additional languages in roadmap — Rust, Ruby? | Confirm current coverage (APP-Q1 mentions them); roadmap note is future work, not TD-bound. |
| C14 (Ahmed) | Positive feedback ("easy to customize and iterate") | Thank and close. |
| C20 (Robert) | Example of sync vs async distinction | Lucas already replied with examples; archetype calibration (Step 2 INF-Q4) already handles this — link to the existing calibration table. |
| C21 (Robert) | CloudTrail in WAFR (→ R5) | Covered by R5 rejection rationale. |
| C25 (Robert) | Comment-resolution process | Process ack, no TD change. |
| C28 (Maia) | Business metrics auto-scaling (→ F6) | Confirm intent tracked as F6 pending R3. |
| C36 (Maia) | Why focus on error budget tracking | Respond with OPS-Q3 positioning; defer any rebalancing. |
| C37 (Robert) | Secrets Management scoring context | Confirm SEC-Q5 rubric is intentional — respond in thread. |

---

## 📚 Already resolved (per analysis doc or prior responses)

Per analysis doc's reasoning: C1 (Agent Storming — ARA, not MOD), C14 (positive), and threads already closed. Listed in the CR description for completeness. No TD work.

Analysis-doc cross-reference table (for reviewer look-up):

| Analysis ID | Topic | Tracked as |
|-------------|-------|-----------|
| C2 | Remove App Mesh | D1 |
| C3 | Scope clarification | A1 |
| C4 | S3 access patterns | E1 |
| C7 | AppSync + IoT Core | D2 |
| C8 | IaC / Terraform consistency | R2 (rejected) |
| C9 | Async-only bias | B3 — archetype calibration already handles; note makes it visible |
| C10 | INF-Q10 look-for scope | B14 |
| C11 | appspec.yml / CodeDeploy | D3 |
| C12 | Language scoring tone | R1 (rejected reframe) + B11 (tone-only fix) |
| C13 | Multi-region backup wording | F2 |
| C15 | Multi-AZ statelessness | B13 |
| C16 | MWAA | D4 |
| C17 | Amazon MQ | D5 |
| C18 | Neptune, Timestream | D6 |
| C19 | Define "tiers" | C1 |
| C22 | WAR → WAFR | docx-only (see docx table) |
| C23 | SEC-Q2 Score overlap | B12 |
| C24 | Plaintext credentials = blocker | R4 (rejected, recommendation-copy counter) |
| C26 | Managed networking services (VPC Lattice, PrivateLink, IPAM) | G3 (pending Maia) |
| C27 | "Made it more agnostic" (Maia direct edit Apr 24) | P0.6 — verify in docx/TD |
| C30 | "compute tiers" | C1 |
| C31 | Version update process | F3 |
| C32 | Key management + rotation | F4 |
| C33 | SCP tagging fix | F1 |
| C34 | DMS/SCT misplaced | E3 |
| C37 | CI/CD covers app + IaC | E4 |

---

## 🔍 Part 3 — Verification

- [ ] **V1 — Grep stale terms:**
  - `compute tiers` — 0 hits (after C1)
  - `App Mesh` — 0 hits in MOD TD (after D1). ARA TD depends on P0.7 decision.
  - `primary database` / `Primary database` — audit remaining hits
  - `in IaC` — unchanged (R2 rejected)
- [ ] **V2 — Spot-check rubrics** INF-Q1, INF-Q2, INF-Q7, INF-Q9, APP-Q1, APP-Q2, APP-Q5, SEC-Q2, SEC-Q3, SEC-Q5, SEC-Q7 for coherent 1→4 progression.
- [ ] **V3 — Confirm no duplicate wording** from P0.4 merge on INF-Q2 Score 2.
- [ ] **V4 — Read CI/CD and INF-Q7 sections end-to-end** post-edit.
- [ ] **V5 — Cross-check portfolio TD.** `portfolio-modernization/transformation_definition.md` references question IDs only (verified) — no rubric text share. Confirm no drift.
- [ ] **V6 — Cross-check example reports.** `example-reports/v2-full-assessment/modernization-assessment/*.md` — low risk per validation report. Flag as stale in CR if any scores shift.
- [ ] **V7 — Confirm no rubric-count change without scope decision.** If G1/G2 add new questions, update category score math, N/A mappings, and the "37 questions across 5 sections" counter in Summary.

---

## 📦 Part 4 — Wrap-up

- [ ] **W1 — Final review.** `git status` + `git -P diff --stat`.
- [ ] **W2 — Raise CR.** Description should include:
  - Link to `feedback-mod-action.md`, `kiro-feedback-changes.md`, and `mod-feedback-analysis.md`
  - Analysis-doc cross-reference table (Part "Already resolved")
  - R1–R5 called out as rejected/reworked with rationale — reviewers can push back on those specifically
  - Phase F status (which F items shipped, which deferred)
  - Phase G status (scope decisions settled or deferred)
  - Call out reopened threads (analysis-C10, C13, C23) explicitly — Robert wants to see these addressed
- [ ] **W3 — Reply in doc threads** for the reply-only items (C5, C14, C20, C21, C25, C28, C36, C37).

---

## MOD Commit Strategy

| Commit | Phases | Message |
|--------|--------|---------|
| A | Phase A + B | `refactor(mod-td): sharpen scoring rubrics, fix APP-Q1 tone, resolve reopened rubrics (P1C, P2A, P4-1, analysis-C10/C12/C15/C23)` |
| B | Phase C + D | `feat(mod-td): add missing AWS services and clarify terminology (P2B, P3)` |
| C | Phase E | `docs(mod-td): expand DATA-Q1 coverage, broaden modernization strategies (P4, WF)` |
| F | Phase F | `feat(mod-td): incorporate Herrera Soto pass — tagging, multi-region, key management, versioning, pipeline security (F1–F6)` |
| G | Phase G (if adopted) | `feat(mod-td): add IaC governance question and resilience testing coverage (G1–G3)` |

Commits A–C are low-risk and can land together. F adds rubric content but no scope change. G is a scope change and should be a separate CR if adopted.

---

## Risk Notes

- **Line numbers drift** — match on FIND text, not line numbers.
- **P0.4 merge** — INF-Q2 has two overlapping edits; apply merged wording once.
- **B4, R3, F6 all touch INF-Q7** — sequence B4 (rubric scores 2/3) → R3 rework (question + rubric broadening) → F6 (business-metrics signal at Score 4). Apply in that order to avoid stomping edits.
- **B9 semantic shift** — SEC-Q7 Score 2/1 rework. Confirmed not a pathway trigger. Safe.
- **R1–R5 rejections are visible** — surface each in CR description so reviewers can push back.
- **Phase G changes question count** — if G1 or G2 lands, update Summary counter, category math, N/A mappings before shipping.
- **Part 3 scope discipline** — if pressed to include docx-only items, hold the line. The TD cycle does not own narrative positioning.

---

# 🤖 ARA — Proposed Feedback Adoption

**TD target:** `agentic-readiness-assessment/transformation_definition.md` (1654 lines)
**Source:** `quick-scripts/feedback-updates/ara-feedback-analysis.md` (34 threads, 57 comments; 8 resolved, 26 open)

> **Note:** This TODO only tracks changes to the **transformation_definition.md**. Many reviewer items target the companion docx (Customer Positioning, How to Use This Guide, Programs table, Appendix narratives). Those are listed separately under "📄 Docx-only" for visibility but are NOT TD work and should be handled in the docx review pass, not here.

---

## Specialist Observations Before Proposing Anything

Three findings from reading the TD + analysis together shape every decision below:

1. **Question numbering mismatch.** The analysis doc's "AUTH-Q5 = Agent-as-Self vs Agent-on-Behalf-of-User" does not match the TD. In the TD, identity propagation is **AUTH-Q4** (RISK); **AUTH-Q5** is credential management (RISK). C11, C31, and any severity discussion that references "AUTH-Q5 identity semantics" actually target **AUTH-Q4**. Fix reviewer-facing numbering before responding, or reviewers will think we ignored their thread.

2. **MCP is already scoped OUT.** Line 165 of the TD reads: *"This assessment does NOT cover agent architecture (…RAG pipelines, MCP servers)…"*. C12, C14, C15, and C33 ask for MCP to be treated as a first-class target. That's a scope reversal, not a wording tweak. Needs a deliberate decision before any edit.

3. **AUTH-Q4 has a duplicated "Look for" block** (TD lines 702–727 are a copy-paste merge artifact). Unrelated to feedback — a hygiene fix we should sneak in while editing this section.

---

## ✅ Part A — TD Adopt (specialist-endorsed, stays within ARA's scope)

All items below change the **transformation_definition.md**.

- [ ] **ARA-A1 — C34 (Riggs): Add "AgentCore Identity" to AUTH-Q1 look-for.**
  AUTH-Q1 is BLOCKER for machine identity. AgentCore Identity is an AWS-native implementation path. Add to the look-for bullet list as a detection signal. Does NOT mean we assess AgentCore specifically; it means we recognize its presence as evidence that machine identity is satisfied.

- [ ] **ARA-A2 — C31 (Riggs): Subject/actor semantics in AUTH-Q4 why-it-matters.**
  *(Reviewer said "AUTH-Q5" but current TD has this at AUTH-Q4 — Identity Propagation and Delegation.)*
  AUTH-Q4 already distinguishes agent-as-self vs agent-on-behalf-of-user. Riggs's phrasing — *"user is the subject, agent is the actor"* — is a cleaner way to say the same thing. Adopt as a why-it-matters rewrite; **do not change severity**.

- [ ] **ARA-A3 — C24 (Riggs + RP): Dual-purpose framing in Objective.**
  Current Objective mentions "safe, operable, integrable." Add one sentence explicitly naming the two use modes: (1) portfolio-level telemetry of which systems are agent-ready, (2) use-case-level dependency checking for a specific agent workflow. RP endorsed both uses.

- [ ] **ARA-A4 — C26 (Harish): Mention "remediation" in Summary.**
  The Summary lists what the output contains but doesn't preview that the assessment *produces remediation guidance*. One-clause addition: findings include prioritized remediation guidance.

- [ ] **ARA-A5 — C25 (Henry): Design-time vs runtime clarification in Summary or Objective.**
  The ARA scans code and config — it doesn't see runtime posture. Make this explicit: *"ARA is a design-time architecture review — it evaluates whether controls exist in code and configuration, not whether they're effective at runtime."* Deflects pentest/runtime-scan requests.

- [ ] **ARA-A6 — C22 + C29: Extend "does NOT cover" list (TD line 165).**
  Current exclusion lists agent architecture and general cloud modernization. Add: "agent-level AI governance (model policy, prompt injection defense, safety evaluation)." Keep to a clause — names the boundary without promising integration.

- [ ] **ARA-A7 — C17 (Harish): HITL framing in Step 5 intro.**
  Current Step 5 intro may sound like ARA is discouraging HITL. Add a line to the Step 5 preamble: *"ARA measures whether the system can support human-in-the-loop patterns — not whether HITL should be mandatory. HITL is a valuable safety mechanism for high-stakes operations."* No rubric impact.

- [ ] **ARA-A8 — Housekeeping: Fix AUTH-Q4 duplicated "Look for" block.**
  TD lines 702–727 have a copy-paste merge artifact — the "Look for" list appears twice with a garbled sentence between them. Clean up while editing the section.

**Commit ARA-TD-1:** `refactor(ara-td): clarify scope, dual-purpose framing, HITL, and AUTH look-for (C17, C22, C24-C26, C31, C34) + AUTH-Q4 cleanup`

---

## 🤔 Part B — TD Adopt with revision (reviewer intent right, needs careful wording)

- [ ] **ARA-B1 — C30 (Riggs): Control-layer note in scope/Summary.**
  A control can live in the application, the platform (API Gateway, service mesh, IAM), or the agent architecture. The TD already acknowledges this in AUTH-Q2 ("enforcement can happen at the platform layer") but only there. Add one line to Summary: *"Controls may exist at the application layer, platform layer, or agent architecture layer. ARA checks end-to-end presence — who implements the control is a design decision."* **Do not invent a new taxonomy.**

- [ ] **ARA-B2 — C12 counter-proposal: MCP-awareness clause in Step 2 intro (API dimension).**
  We reject evaluating MCP (see R1 below) but can acknowledge it in one line at the top of the API section: *"When MCP-native integration is the target, the findings here inform what an MCP server wrapping this system will need to expose."* Signals we see the question; doesn't import MCP rubrics.

- [ ] **ARA-B3 — C33 partial: AUTH-Q2 why-it-matters — scoped permissions phrasing.**
  Riggs's phrasing about "cannot scope down agent access" is useful for AUTH-Q2 (Scoped Permissions). Adopt the scoped-access language for AUTH-Q2 why-it-matters; **drop** the MCP reference from his proposed wording.

- [ ] **ARA-B4 — C11 counter-proposal: Multitenancy cross-reference in AUTH-Q4.**
  Justin's concern about multitenancy + identity propagation is real, but severity escalation is wrong (see R2). Add a paragraph to AUTH-Q4 why-it-matters: *"When the target system serves multiple tenants, weak identity propagation compounds with data-layer risks (DATA-Q2 data residency, DATA-Q6 PII in logs). Treat these as a cluster when planning remediation."* **No severity change.**

**Commit ARA-TD-2:** `docs(ara-td): control-layer note, MCP awareness clause, multitenancy cross-reference (C11, C12, C30, C33)`

---

## ❌ Part C — TD Reject (scope mismatch; counter-proposals already in Part B)

- [ ] **ARA-R1 — C12/C14/C15 (Mark + RP): "Evaluate MCP interfaces as a first-class target."**
  **Reject.** The TD explicitly excludes MCP servers from scope (line 165). Agent architecture — which MCP is — is not what ARA evaluates; ARA evaluates what agents *call*. If we added MCP rubrics, we'd need new scoring across API-Q1–Q4 and AUTH-Q4. That's a scope reversal requiring leadership sign-off.
  **Counter-proposal:** ARA-B2 (one-line awareness clause in Step 2).
  **Respond in docx thread:** "Current API surface is assessed because that's what agents call today. MCP is covered by bridge-mode guidance and agent architecture (out of scope per intro)."

- [ ] **ARA-R2 — C11 (Justin): Escalate AUTH-Q4 severity beyond RISK.**
  **Reject severity change.** The severity model is deliberate:
  - AUTH-Q1 (Machine Identity) = BLOCKER handles the categorical "no identity = no multitenancy" case.
  - AUTH-Q4 = RISK-SAFETY handles the "identity exists but propagation is weak" case. This maps to Pilot-Ready (1–2 RISK-SAFETY) by design.
  - Escalating AUTH-Q4 would push many repos from Pilot-Ready to Remediation Required on architecture maturity, not actual agent-safety risk.
  **Counter-proposal:** ARA-B4 (multitenancy cross-reference, no severity change).

- [ ] **ARA-R3 — C33 MCP reference.**
  **Partial reject.** Scoped permissions phrasing is adopted in ARA-B3. MCP reference is dropped (same reasoning as R1).

---

## 📄 Docx-only items (NOT TD work — track in docx review pass)

These reviewer comments address the narrative docx (Customer Positioning, How to Use This Guide, Programs table, Appendix). They do **not** belong in the TD edit cycle. Listed here only so nothing gets lost when the CR description references the analysis doc.

| Analysis ID | Topic | Docx location |
|-------------|-------|---------------|
| C16 | EBA hyperlink | Appendix 3 Programs table |
| C21 | Self-serve + managed delivery model | Customer Positioning section |
| C19 | "Relationship to OLA" — assessment fatigue | How to Use This Guide (new section) |
| C27 | MOD cross-reference (docx narrative) | Intro / opening narrative |
| C18 | "When to run" timing guidance | How to Use This Guide |
| C23 | "target systems" vs "source systems" glossary | Docx glossary |
| C29 (part) | Delineation from "AI team's readiness assessment" | Intro narrative |

---

## 💬 Reply-only items (neither TD nor docx edits — respond in reviewer thread)

| Analysis ID | Topic | Suggested response |
|-------------|-------|--------------------|
| C32 | "Why RISK not BLOCKER?" | *"AUTH-Q2/Q3 are RISK-SAFETY because the control can be enforced at the platform layer (API Gateway, IAM) even if the app is coarse-grained. BLOCKER is reserved for categorical failures like no machine identity at all."* |
| C28 | "Does it assess data exposure, privilege escalation, destructive actions?" | Respond with mapping: data exposure → DATA-Q1/Q2/Q6; privilege escalation → AUTH-Q2/Q4; destructive actions → STATE-Q1/Q5/Q6. All already covered. |
| C13 | "guarantees?" | Needs anchor identification in docx before responding. |
| C14 | "but does look at MCP interface definitions?" | Covered by R1 response. |
| C15 | "why not MCP server interfaces?" | Covered by R1 response. |
| C10 | "Post-readiness POV — what comes next?" | Point to AI DLC workshop (already referenced in docx) and any agent-side readiness assessment. Explicitly out of ARA scope. |
| C9 | "Example of what you mean?" | Blocked — need to identify the comment anchor in docx. |

---

## 📚 Already resolved (per analysis doc 🟢 RESOLVED list — no work)

C1 (Agent Storming), C2 (FinOps), C3 (multi-agent framing), C4 (portfolio metrics), C5 (Gartner citation), C6 (process modeling), C7 (EBA criteria), C8 (AI DLC). Listed for CR completeness only.

---

## ⚠️ ARA Pre-flight

- [ ] **ARA-P0.1 — Reconcile question numbering with reviewers.** Analysis doc says "AUTH-Q5: Agent-as-Self vs Agent-on-Behalf-of-User" — actual TD has this at AUTH-Q4. Map both in the CR description so C11/C31 replies hit the right question.
- [ ] **ARA-P0.2 — Retrieve docx anchors for C9 and C13.** Both need comment-position lookup in the source docx before a response can be drafted.
- [ ] **ARA-P0.3 — Scope decision: is MCP in or out?** Today the TD says out (line 165). Part C rejects MCP evaluation; Part B adds one awareness clause. If leadership decides MCP should be evaluated, Parts B2 and C1/C3 flip. **Do not execute until this is settled.**
- [ ] **ARA-P0.4 — Confirm no rubric changes.** Nothing in Parts A or B changes severity, readiness profile math, N/A mappings, or pathway triggers. Verify before CR.

---

## ARA Commit Strategy

| Commit | Scope | Message |
|--------|-------|---------|
| ARA-TD-1 | Part A (8 items) | `refactor(ara-td): clarify scope, dual-purpose framing, HITL, AUTH look-for + AUTH-Q4 cleanup (C17, C22, C24-C26, C31, C34)` |
| ARA-TD-2 | Part B (4 items) | `docs(ara-td): control-layer note, MCP awareness clause, multitenancy cross-reference (C11, C12, C30, C33)` |

---

## Why I'm drawing these lines

ARA has a tight, deliberate scope: *"Evaluate whether target systems are safe, operable, integrable by agents."* Three scope guardrails keep it useful:
1. **Target systems, not agents.** Reviewing MCP servers, prompt injection, agent governance, or model policy breaks this guardrail.
2. **Design-time, not runtime.** Reviewing live posture or live credentials breaks this guardrail.
3. **Severity-based, not numeric.** BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO maps to readiness profile. Mixing numeric scoring in (as C11/C32 implicitly push toward) breaks the profile math.

Parts A and B strengthen ARA within these guardrails. Part C rejects items that would cross them — each with a counter-proposal folded into Part B so reviewers see their concern addressed, not dismissed. Docx-only and reply-only items are split out so we're not editing the TD to answer narrative questions.
