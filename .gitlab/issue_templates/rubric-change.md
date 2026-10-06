<!--
  Defect / change report for the managed Transformation Definitions and their scorer.
  Use this to PROPOSE a rubric change OR report a scoring defect before opening an MR —
  for floating an idea, gathering agreement, or flagging a gap you noticed.

  FIRST decide what KIND of defect this is (§0). It decides who fixes it, which label
  it gets, where the fix lives, and whether an Benchmark re-publish is owed. The most
  common mistake is filing a *judge* artifact as a *TD* bug: before concluding the TD
  is wrong, confirm the report's own recorded scope / surface_flags don't ALREADY
  justify the output (§1). Real example — a "fabricated" deployment finding was
  actually correct because has_deployed_workload=true; the judge, not the TD, was
  wrong (#9).

  Background: TDs live in definitions/managed/<td>/ (SKILL.md + references/), directly
  editable here; the external scorer prompts are harness/rubric/*-scorer-prompt.md.
  New to this? Read docs/contributing/README.md. Harness internals: harness/DESIGN.md.
-->

## 0. What kind of defect is this?
<!-- Tick ONE, then apply the matching label (this template no longer auto-labels). -->
- [ ] **TD rubric** — the Task Definition's scoring / wording / gating is wrong → fix in `definitions/managed/<td>/`, label ~td-change
- [ ] **Grader / scorer (judge)** — the TD is right but the judge mis-scored the report (e.g. it ignored a recorded `surface_flag`, or invented a "fabrication") → fix in `harness/rubric/*-scorer-prompt.md` and/or the in-repo grader, label ~judge
- [ ] **Harness / tooling** — should-run, diff, digest, rebaseline, pipeline, or baseline plumbing → label ~bug

## 1. Evidence — and rule out a judge artifact first
<!-- Ground it; don't paraphrase. Fill what applies:
     - Fixture + analysis + score:  e.g. modern-orders-service (MOD) 0.72
     - question_id(s):              e.g. DATA-Q1
     - The report's OWN recorded scope / surface_flags for that question — does anything
       there already justify the current output? If YES, this is a ~judge issue (§0),
       NOT a TD bug. (This is the check that would have caught #9.)
     - TD file:line the rule lives at, or is missing from:  e.g. mod/references/01-question-bank.md:578
     - Reproducibility: does it survive re-rolls (a DETERMINISTIC defect) or is it a
       single draw (WITHIN-NOISE)? The rebaseline digest separates these — cite which. -->



## 2. Why? (what's wrong, and the correct behavior)
<!-- What the TD / judge currently gets wrong, and what it should do instead. -->



## 3. Expected impact
<!-- Which dimension(s) should move: more/fewer findings (D1)? ARA tier (D2)?
     MOD pathway trigger (D3)? portfolio program (D4)? MOD score-band crossing (D5)?
     A rough guess is fine at the issue stage. -->



## 4. Fix shape
<!-- Prefer a DETERMINISTIC offline check over model calibration wherever the defect is
     mechanically checkable (counts, gate-vs-finding consistency, band-vs-tier) — those
     don't drift and fail loudly. Reach for prose only when judgment is unavoidable.

     IDs ARE PERMANENT. A question_id is a stable key, not a position — everything
     downstream (goldens, priority table, portfolio rollup) joins on it. When adding or
     removing, you MUST update the count literal (43 ARA / 37 MOD) in the same MR or CI
     fails loudly. See docs/contributing/README.md → "Add or remove a question". -->
- [ ] Deterministic offline check / grader gate
- [ ] Calibration or wording prose
- [ ] Re-score an existing question (severity / wording / criteria — no count change)
- [ ] **Add** a question — append the next free ID in its category (never reuse a retired one); **+1** the count literal
- [ ] **Remove** a question — delete it and **leave the gap** (never renumber Q4→Q3, it silently reassigns findings); **−1** the count literal

## 5. Benchmark re-publish on fix?
<!-- The external scorer prompts are hand-published to Benchmark. GEN blocks (severity /
     question / tier tables) auto-regenerate via harness:scorer-sync; HAND-OWNED prose
     (calibration, extended triggers, N/A rules) does NOT. If the fix touches that prose,
     a MANUAL re-publish is owed after merge — call it out here so it isn't forgotten. -->
- [ ] YES — manual re-publish owed (fix touches hand-owned scorer-prompt prose)
- [ ] NO — no scorer-prompt prose change

---

<!-- Next: once there is agreement here, open a Merge Request with the rubric-change MR
     template. The pipeline publishes the edited TD, runs it over the fixtures, and posts
     an advisory judge verdict. Set the label above to match your §0 choice. -->
