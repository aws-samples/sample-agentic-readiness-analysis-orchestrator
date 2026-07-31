<!--
  TD change MR — proposing an edit to a managed Transformation Definition:
  definitions/managed/<td>/SKILL.md (or its references/). e.g. add a question,
  re-score one, adjust a pathway trigger, or a program-recommendation rule.

  This template captures your INTENT. The change-impact harness runs on this MR
  (should-run.sh -> run-fixtures.sh publishes + execs your edited TD -> diff-reports.py
  -> judge.py) and an LLM-as-judge posts an ADVISORY verdict comparing the observed
  delta against what you say below, plus a quality-regression read and suggestions.
  The verdict is advisory only — it never blocks the MR. See harness/DESIGN.md (§6, §8.1).

  Fill in every section below — the judge reads them as intent.{what, why, expected_impact}.
-->

## What are you changing?
<!-- Be specific: name the TD, the question_id(s)/pathway/program, and the exact edit.
     e.g. "modernization-readiness-analysis: tightened INF-Q11 scoring so missing IaC now fails."
     e.g. "agentic-readiness-analysis: added AUTH-Q9 for token-rotation gaps (new RISK-SAFETY question)." -->



## Why?
<!-- The problem this fixes. What does the current TD get wrong or miss?
     e.g. "Unauthenticated write surfaces were scoring too low; they are a safety risk for agents." -->



## Was the rubric edited in the AWS Transform service?
<!-- The judge reads this to tell "the edit didn't land" apart from "the goldens are stale".
     If you edited the rubric in-service rather than in this repo, the fixtures here run the
     REPO copy, so the delta can come back empty even though your change is real. -->

- [ ] yes — the change was made in-service (fire `harness:full` manually to refresh goldens)
- [ ] no — the change is in this repo's SKILL.md

## Expected impact
<!-- Which harness dimension(s) should move, and in which direction?
     D1 Findings      — more/fewer/re-severitied findings, in which categories?
     D2 Tier          — should any repo/portfolio change readiness tier? which way?
     D3 Pathways (MOD)— should a pathway newly trigger or stop triggering?
     D4 Programs      — should a portfolio program (AI DLC, AXE, EBA, MAP, OLA…) start/stop triggering?
     D5 Score (MOD)   — should a category/overall score cross a band (Not Ready/Needs Work/Partial/Mature)?
     e.g. "Expect more AUTH RISK-SAFETY findings on legacy-shipping-api and a possible
           ARA tier drop from Pilot-Ready to Pilot-Ready (Safety Concerns)." -->



---

<!-- After you open this MR, the GitLab pipeline publishes your edited TD as a custom def,
     runs it over the fixtures, diffs vs the golden baseline, and posts an advisory judge
     verdict as a comment (score + LGTM/needs-work + intent-match + quality-regression flag +
     rationale citing specific question_ids / pathway ids / program acronyms). It never blocks
     the MR. On approval, a maintainer publishes the change to AWS Transform Continuous
     Modernization (the deploy surface) — this repo is the proposal + test surface. -->

/label ~td-change
