<!--
  Thanks for the contribution! This is the general PR template for the GitHub mirror.

  Heads up: the change-impact harness (re-runs the analysis, diffs the result, posts an advisory
  judge verdict) runs on the internal AWS GitLab mirror ONLY — it needs AWS credentials. A GitHub
  PR gets human review but NO automated harness verdict. If your change touches a rubric or the
  harness, an internal maintainer takes it through the harness on the GitLab side.

  Changing what a Transformation Definition scores? Read docs/contributing/README.md first.
-->

## What does this PR change?



## Why?



## Type of change

- [ ] Rubric / TD change (a question, severity, pathway, program, threshold)
- [ ] Change-impact harness / CI
- [ ] Orchestrator (`orchestrator/SKILL.md` / references)
- [ ] Documentation / examples
- [ ] Other

## Checklist

- [ ] I read the relevant part of [`docs/contributing/README.md`](docs/contributing/README.md) if this touches a rubric.
- [ ] Local tests pass: `python3 -m pytest harness/tests/ -q`.
- [ ] **Add/remove a question?** I updated the one count literal (43 / 37) in `harness/tests/test_skill_table.py` in this PR, and left question IDs permanent (no renumbering to close a gap).
- [ ] **Rubric change?** I updated the benchmarking scorer prompts (`harness/rubric/ara-scorer-prompt.md` / `mod-scorer-prompt.md`) if the change affects them.
- [ ] I did **not** hand-edit any generated file (`harness/SCORES.md`, `harness/golden-accuracy-baseline.json`, golden trees).
- [ ] If this relaxes a safety signal (a severity demotion, a moved/removed `⚡` marker), I called it out explicitly above so reviewers and the judge can weigh it.

<!-- Internal contributors: push to the `gitlab` remote to get the advisory harness verdict. -->
