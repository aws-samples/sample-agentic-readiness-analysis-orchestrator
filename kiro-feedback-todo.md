# TODO — Apply Reviewer Feedback to MOD Transformation Definition

**Source:** `kiro-feedback-changes.md`
**Target:** `modernization-assessment/transformation_definition.md`
**Total tasks:** 25 TD edits + verification

---

## How to work this list

1. Work tasks in the order below. Order is chosen to minimize conflicts and line-number drift.
2. For every edit, match on the FIND text from `kiro-feedback-changes.md` — **ignore the line numbers** in that doc (they drift as soon as edits land).
3. Check off tasks as you complete them. Commit in logical groups (see "Commit Checkpoints" below).
4. Before starting: `git status` should be clean. Create a branch.

---

## ⚠️ Pre-flight — Resolve Conflicts First

Before touching the TD, reconcile these in `kiro-feedback-changes.md`:

- [ ] **C0.1 — Merge P2A-2 and WF-1 (INF-Q2 Score 2 duplicate).**
  Both rewrite `| **2** | Mix of managed and self-managed, or managed but single-AZ without failover. |`. WF-1 wording ("Main production databases...") is preferred over P2A-2 ("Primary databases..."). Apply WF-1's wording with P2A-2's structure. Decide final text and remove one of the two tasks from the work plan.
- [ ] **C0.2 — Decide direction on Task 9 ("in IaC" → "Terraform/CloudFormation").**
  This change makes two lines more specific while leaving dozens of other "in IaC" references untouched — net result is *less* consistency. Options:
  - (a) Keep the task as-is (accept the inconsistency).
  - (b) Drop the task.
  - (c) Expand: apply doc-wide.
  Pick one before executing.
- [ ] **C0.3 — Confirm P4-3 is a 3-part edit.**
  P4-3 has three FIND/REPLACE blocks for INF-Q7 (question, why-it-matters, look-for). Treat as three sub-tasks when applying.
---

## Phase 1 — Pre-flight on the TD

- [ ] **T00.1** — `git checkout -b feedback/mod-td-reviewer-pass`
- [ ] **T00.2** — Read `modernization-assessment/transformation_definition.md` end-to-end once for orientation (1712 lines).
- [ ] **T00.3** — Confirm all FIND strings from `kiro-feedback-changes.md` actually exist in the TD. Grep each one; if any FIND is missing, flag before editing anything.

---

## Phase 2 — P1 Changes (scope + structural)

Do these first — they change framing and scope, which anchors everything below.

- [ ] **T01 — P1C-1: Add AWS scope statement and on-prem/multi-cloud exclusion.**
  FIND `This assessment does NOT cover:` → prepend AWS-scope paragraph per changes doc.
- [ ] **T02 — P1B / Task 10: Reframe APP-Q1 from "language modernity" to "SDK + agent framework coverage."**
  Largest single edit. Replaces the entire APP-Q1 question + rubric + look-for block (~14 lines).

---

## Phase 3 — P2-A Scoring Precision (signal-based rewrites)

These sharpen rubrics. Safe to do in any order but done together to land as a coherent commit.

- [ ] **T03 — P2A-1: INF-Q1 Score 4** — "80%+ of compute" → service-count-based criterion.
- [ ] **T04 — P2A-2 + WF-1: INF-Q2 Scores 2 and 3** (merged per C0.1).
  - [ ] Score 3: "Primary databases managed..." → "Main production databases managed..."
  - [ ] Score 2: Apply the merged wording (WF-1 phrasing with P2A-2 structure).
- [ ] **T05 — P2A-3: INF-Q4** — prepend archetype-visibility note above `**Archetype Calibration:**`.
- [ ] **T06 — P2A-4: INF-Q7 Scores 3 and 2** — differentiate by scaling-policy sophistication (custom vs default).
- [ ] **T07 — P2A-5: APP-Q2 Scores 3 and 2** — differentiate by schema separation and circular deps.
- [ ] **T08 — P2A-6: APP-Q5 Scores 3 and 2** — define "inconsistent" (most-follow vs <50%).
- [ ] **T09 — P2A-7: SEC-Q3 Scores 3 and 2** — differentiate by auth method vs coverage.
- [ ] **T10 — P2A-8: SEC-Q5 Scores 3 and 2** — differentiate by what's in env vars.
- [ ] **T11 — P2A-9: SEC-Q7 Scores 2 and 1** — eliminate overlap between "no scanning" and "scanning not in pipeline."

**Commit checkpoint A** — after T02–T11. Message: `refactor(mod-td): sharpen scoring rubrics per reviewer feedback (P1B, P2A)`.

---

## Phase 4 — P2-B Terminology Fixes

- [ ] **T12 — Task 7: "compute tiers" → "compute resource types"** (INF-Q7 Score 4).
- [ ] **T13 — Task 9: "in IaC" → "Terraform/CloudFormation"** — only if C0.2 decision is (a) or (c). Skip if (b).
  - [ ] Line ~166: AWS CodePipeline definitions
  - [ ] Line ~172: Container image references
- [ ] **T14 — WF-1 leftovers: remaining "primary database" → "main production database"** wording fixes.
  - [ ] INF-Q8 Score 2
  - [ ] INF-Q9 Score 3
- [ ] **T15 — WF-2: "containerize as-is" → "containerize, migrate to serverless (Lambda), ..."**
- [ ] **T16 — WF-3: SEC-Q3 Score 4** — clarify for intentional public APIs.

---

## Phase 5 — P3 Missing AWS Services

- [ ] **T17 — Task 1: Remove App Mesh references** (deprecated Sept 2026).
  - [ ] Service mesh configs line (~192)
  - [ ] Look-for line (~714)
- [ ] **T18 — Task 2: Add AppSync + IoT Core to INF-Q6.**
  - [ ] Question line (~525)
  - [ ] Look-for line (~536)
- [ ] **T19 — Task 3: Add `appspec.yml` (CodeDeploy) to CI/CD discovery.**
  - [ ] CI/CD file patterns (~165)
  - [ ] Look-for line (~611)
- [ ] **T20 — Task 4: Add MWAA to INF-Q3** workflow orchestration list.
- [ ] **T21 — Task 5: Add Amazon MQ to INF-Q4** messaging/streaming list.
  - [ ] Question line (~491)
  - [ ] Look-for line (~506)
- [ ] **T22 — Task 6: Add Neptune + Timestream to INF-Q2** managed DB list.
  - [ ] Question line (~457)
  - [ ] Look-for line (~468)

**Commit checkpoint B** — after T12–T22. Message: `feat(mod-td): add missing AWS services and update terminology (P2B, P3)`.

---

## Phase 6 — P4 Content Enhancements

- [ ] **T23 — P4-1: Name the 5 dimensions early** (Infrastructure, Application Architecture, Data Platform, Security, Operations).
- [ ] **T24 — P4-2: Add S3 access-pattern assessment to DATA-Q1.**
- [ ] **T25 — P4-3: Broaden INF-Q7 beyond compute auto-scaling** (3-part edit per C0.3).
  - [ ] Question line
  - [ ] Why-it-matters line
  - [ ] Look-for line
- [ ] **T26 — P4-4: Highlight S3 Files as FS-access solution** (DATA-Q1 Score 2 note).
- [ ] **T27 — P4-5: Remove misplaced DMS/SCT reference from INF-Q2 why-it-matters.**
- [ ] **T28 — P4-6: Clarify CI/CD covers app AND IaC pipelines.**

**Commit checkpoint C** — after T23–T28. Message: `docs(mod-td): expand coverage per reviewer suggestions (P4)`.

---

## Phase 7 — Verification

- [ ] **T29 — Search the TD for stale references to removed terms:**
  - `App Mesh` — should be 0 hits
  - `compute tiers` — should be 0 hits
  - `primary database` — audit remaining hits; confirm intentional
- [ ] **T30 — Spot-check rubric tables** for INF-Q1, INF-Q2, INF-Q4, INF-Q7, APP-Q1, APP-Q2, APP-Q5, SEC-Q3, SEC-Q5, SEC-Q7. Each should read as a coherent 1→4 progression after edits.
- [ ] **T31 — Confirm no trailing duplicates** (e.g., "Main production databases" appearing twice in the same score row from overlapping edits).
- [ ] **T32 — Read the CI/CD and INF-Q7 sections end-to-end** — these have the most compound edits.

---

## Phase 8 — Wrap-up

- [ ] **T33** — Final `git status` + `git -P diff --stat` review.
- [ ] **T34** — Raise CR (`cr`) with summary of reviewer feedback addressed; link back to reviewer threads (C3, C5, C6, C13, C17, C19, C22, C26, C28, C30, C32, C34, C36, C37, C42/43, C45, C46, C47 + Robert's threads 1, 7, 9, 12, 13, 20, 21, 24, 30, 36).

---

## Commit Strategy Summary

| Checkpoint | Tasks | Commit Message |
|------------|-------|----------------|
| A | T02–T11 | `refactor(mod-td): sharpen scoring rubrics per reviewer feedback (P1B, P2A)` |
| B | T12–T22 | `feat(mod-td): add missing AWS services and update terminology (P2B, P3)` |
| C | T23–T28 | `docs(mod-td): expand coverage per reviewer suggestions (P4)` |
| — | T01 | Standalone or rolled into A: `docs(mod-td): clarify AWS scope and exclusions (P1C)` |

---

## Risk Notes

- **Line numbers drift.** Match on FIND text only.
- **Three conflict/decision points** sit in the pre-flight (C0.1, C0.2, C0.3) — resolve before T01.
- **P4-3 and P2A-3** each touch multiple places in the same question — do them as single logical units, not one bullet at a time.
- **SEC-Q7 Score 2/1 overlap fix (T11)** changes semantics, not just wording — double-check it doesn't break any scoring references elsewhere in the TD.
