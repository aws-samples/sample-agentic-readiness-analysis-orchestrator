<!--
  TD change idea — use this to PROPOSE a change to a managed Transformation
  Definition before opening an MR. Good for floating an idea, gathering agreement,
  or flagging a scoring gap you have noticed. When the idea is agreed, open a Merge
  Request with the TD-change MR template (which the change-impact harness runs against).

  Background: the TD definitions live in definitions/managed/<td>/ (SKILL.md +
  references/) and are directly editable in this repo. AWS Transform Continuous
  Modernization is the deploy surface. See harness/DESIGN.md.
-->

## What TD / question / category?
<!-- Which TD (agentic-readiness-analysis / modernization-readiness-analysis / their portfolios)?
     ARA categories (AUTH/API/STATE/DATA/OBS/ENG/HITL/DISC) or MOD (APP/DATA/INF/OPS/SEC)?
     Is this a NEW question or a RE-SCORE of an existing question_id (e.g. AUTH-Q5, INF-Q11)? -->



## Why?
<!-- The problem: what does the TD currently miss or get wrong? -->



## Expected impact
<!-- Which dimension(s) should move: more/fewer findings (D1)? a tier change (D2)?
     a MOD pathway trigger (D3)? a portfolio program (D4)? a MOD score band crossing (D5)?
     A rough guess is fine at the issue stage. -->



---

<!-- Next step: once there is agreement here, open a Merge Request using the TD-change MR
     template and edit definitions/managed/<td>/. The pipeline publishes your edited TD,
     runs it over the fixtures, and posts an advisory judge verdict. -->

/label ~td-change
