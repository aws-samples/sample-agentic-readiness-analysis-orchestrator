<!--
  Rubric change MR — proposing a NEW question or RE-SCORING an existing one in
  harness/rubric/ara-questions.yaml or harness/rubric/mod-questions.yaml.

  This template captures your INTENT. The change-impact harness runs on this MR
  (should-run.sh -> fixtures -> diff-reports.py -> judge.py) and an LLM-as-judge
  posts an ADVISORY verdict comparing the observed delta against what you say
  below. The verdict is advisory only — it never blocks the MR. See
  harness/rubric/README.md and harness/DESIGN.md (§6, §8.1).

  Fill in every section below — the judge reads them as intent.{what, why, expected_impact}.
-->

## What are you changing?
<!-- Be specific: name the question_id(s) and the exact edit.
     e.g. "Tightened AUTH-Q5 scoring: missing rate limiting now RISK-SAFETY instead of INFO."
     e.g. "Added AUTH-Q9 for token-rotation gaps (new RISK-SAFETY question)." -->



## Why?
<!-- The problem this fixes. What does the current rubric get wrong or miss?
     e.g. "Unauthenticated write surfaces were scoring too low; they are a safety risk for agents." -->



## Expected impact
<!-- Which harness dimension(s) should move, and in which direction?
     D1 Findings      — more/fewer/re-severitied findings, in which categories?
     D2 Tier          — should any repo/portfolio change readiness tier? which way?
     D3 Pathways (MOD)— should a pathway newly trigger or stop triggering?
     D4 Programs      — should a portfolio program (AI DLC, AXE, EBA, MAP, OLA…) start/stop triggering?
     D5 Score (MOD)   — should a category/overall score cross a band (Not Ready/Needs Work/Partial/Mature)?
     e.g. "Expect more AUTH RISK-SAFETY findings on legacy-shipping-api and a possible
           ARA tier drop from Pilot-Ready to Pilot-Ready (Safety Concerns)." -->



## Was the rubric edited in the AWS Transform service?
<!-- The service is authoritative. Edits made ONLY in this repo produce a git diff the
     harness can see automatically. Edits made directly in the AWS Transform service do NOT
     show up in a git diff — a maintainer must run harness:full and re-baseline the goldens. -->

- [ ] **Yes** — I edited the rubric in the AWS Transform service. A maintainer must run `harness:full` and sync/re-baseline.
- [ ] **No**  — this MR only edits `harness/rubric/*.yaml`; the MR pipeline will run the harness automatically.

---

<!-- After you open this MR, the GitLab pipeline runs the harness and posts an advisory judge
     verdict as a comment (score + LGTM/needs-work + intent-match + rationale citing specific
     question_ids / pathway ids). It never blocks the MR. A maintainer reviews and, on approval,
     manually syncs the approved change into the AWS Transform service. -->

/label ~rubric-change
