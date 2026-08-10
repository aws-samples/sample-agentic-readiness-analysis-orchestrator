# TD Anatomy — where everything lives

Before you edit a rubric, know its shape. Every managed TD is a lean **`SKILL.md` spine**
plus **`references/*.md`** loaded on demand. The harness reads `SKILL.md` + `references/*.md`
concatenated at runtime (`harness/skill_table.py::parse_questions`), so a TD edit takes effect
on the next run with no code change — the sole exception is the question-count bump (see
[change-a-question.md](./change-a-question.md)).

## ARA — `definitions/managed/agentic-readiness-analysis/`

```
SKILL.md                       # spine: name, objective, 8-section summary, flow, "load X here"
references/
├── 01-scoring-model.md        # tiers, severity model, unified severity/category display,
│                              #   RISK-tier assignment, service-archetype, readiness-profile
├── 02-question-bank.md        # all 43 questions (Steps 2–9) — severity, scope, calibration
├── 03-report-template.md      # markdown report: header, profile, counts, BLOCKER/RISK/INFO
└── 04-output-contract.md      # machine-readable 4-artifact contract, ara_metadata, HTML
```

**Where a question's severity lives:** in the **question heading itself**, e.g.
`#### API-Q1: Documented API Interface — BLOCKER`. ARA has exactly **3 unified severities**
(BLOCKER / RISK / INFO, with RISK sub-tiers like RISK-SAFETY / RISK-QUALITY assigned in
`01-scoring-model.md`). To re-score a question, edit the `— SEVERITY` suffix on its heading.

## MOD — `definitions/managed/modernization-readiness-analysis/`

```
SKILL.md                       # spine
references/
├── 01-question-bank.md        # all 37 questions
├── 02-pathways.md             # the 7 modernization pathways + triggers
├── 03-report-template.md      # markdown report structure
└── 04-output-contract.md      # machine-readable contract
```

**Where a question's severity lives:** MOD does **not** carry severity in the heading
(`#### INF-Q1: Managed Compute`). Instead each question has a **1–4 rubric table** scored
against criteria; the classification thresholds and 3 unified severities are defined in the
scoring section. To re-score, edit the 1–4 criteria table for that question.

## Portfolio TDs

`portfolio-agentic-readiness-analysis/` and `portfolio-modernization-readiness-analysis/` each
carry a `SKILL.md` + `references/program-library.md` (the AWS Program & GTM Library, loaded at
runtime). They roll up the per-repo results and attach program recommendations; they do not
define new questions.

## Question IDs are permanent keys

A `question_id` (`AUTH-Q7`, `INF-Q1`) is a stable key, not a position. Everything downstream —
golden baselines, the static priority table, portfolio aggregation, the findings/evaluations
split — joins on `(analysis_type, question_id)`. **Never renumber to close a gap.** The full
rule is in [change-a-question.md](./change-a-question.md) and
[`harness/rubric/README.md`](../../harness/rubric/README.md).

## How the harness sees the TD

The parser concatenates the spine and references, extracts every `#### <ID>: <title>` heading,
and cross-checks the total against `EXPECTED_QUESTIONS = {"ara": 43, "mod": 37}` in
[`harness/skill_table.py`](../../harness/skill_table.py). If a heading drifts so the parser
can't read it, the count assertion fires — that's the guard that stops the judge scoring on a
partial table. See [invariants.md](./invariants.md).

For what the TD emits and how it's scored end-to-end, see
[`harness/DESIGN.md`](../../harness/DESIGN.md) §2–§3.
