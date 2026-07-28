<!--
  Rubric change idea — use this to PROPOSE a rubric change before opening an MR.
  Good for floating an idea, gathering agreement, or flagging a scoring gap you
  have noticed. When the idea is agreed, open a Merge Request with the
  `rubric-change` MR template (which the change-impact harness runs against).

  Background: the rubric proposal surface lives in harness/rubric/*.yaml. The
  AWS Transform service stays authoritative. See harness/rubric/README.md.
-->

## What question / category?
<!-- ARA (AUTH/API/STATE/DATA/OBS/ENG/HITL/DISC) or MOD (APP/DATA/INF/OPS/SEC)?
     Is this a NEW question or a RE-SCORE of an existing question_id?
     Name the question_id if it exists (e.g. AUTH-Q5, INF-Q11). -->



## Why?
<!-- The problem: what does the rubric currently miss or get wrong? -->



## Expected impact
<!-- Which dimension(s) should move: more/fewer findings (D1)? a tier change (D2)?
     a MOD pathway trigger (D3)? a portfolio program (D4)? a MOD score band crossing (D5)?
     A rough guess is fine at the issue stage. -->



---

<!-- Next step: once there is agreement here, open a Merge Request using the
     `rubric-change` MR template and edit harness/rubric/*.yaml. The pipeline runs
     the harness and posts an advisory judge verdict. -->

/label ~rubric-change
