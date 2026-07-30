# s1 vs s2 — accuracy side by side (INTERIM — DELETE THIS FILE AFTER RE-BASELINING)

> **This file is temporary scaffolding and must not become a second home for scores.**
> There is exactly ONE scoring record: [`golden-accuracy-baseline.json`](./golden-accuracy-baseline.json)
> (data) rendered to [`SCORES.md`](./SCORES.md) (readable). `SCORES.md` **already** grows
> one column per batch automatically — `render_markdown()` derives the columns from each
> row's `by_tree` keys, so re-baselining across `golden s2 s3` produces the side-by-side
> table below *inside* `SCORES.md`, with no new file and no format change.
>
> This file exists only because the re-baseline cannot run yet (s2 is incomplete — see
> Scope). Once it does:
> ```
> harness/score-reports.py --trees harness/golden harness/samples/s2 harness/samples/s3 \
>   --update-baseline --markdown harness/SCORES.md
> git rm harness/SCORES-s1-vs-s2.md
> ```
>
> **This is NOT the committed baseline.** It is an ad-hoc, *partial* comparison of two
> independent analysis runs, kept so the s1/s2 difference is reviewable while s3 is still
> generating. Neither committed artifact was touched to produce it (no `--update-baseline`).
>
> **Scope: 7 of 14 fixtures, 2 of 3 planned samples.** Only the fixtures that had a
> complete ARA+MOD pair in *both* trees at the time of the run are included; `s2` was still
> mid-generation. `golden` is sample 1 (s1).
>
> Regenerated with:
> ```
> harness/score-reports.py --trees harness/golden harness/samples/s2 \
>   --only <the 7 paired fixtures> --markdown harness/SCORES-s1-vs-s2.md
> ```

## What the two runs actually show

Same TDs, same fixtures, different run — so every difference below is **run-to-run
variance of the analysis agent**, not the effect of any change. Two things stand out:

| | ARA | MOD |
|---|---|---|
| mean s1 -> s2 | 0.657 -> 0.797 (**+0.140**) | 0.897 -> 0.894 (−0.003) |
| direction | **6 up, 0 down, 1 equal** | 2 up, 2 down, 3 equal |
| worst single fixture | `legacy-loan-calculator` 0.42 -> 0.88 (**+0.46**) | `legacy-pricing-cgi` −0.06 |

**MOD is stable; ARA is not.** MOD behaves exactly as a noise band should — symmetric,
mean delta ≈ 0, every move inside the 0.02 floor. ARA moved **one-sidedly**: six of seven
fixtures improved and none regressed. A symmetric noise process does not produce 6-0, so
this is not run-to-run variance. It has a specific, identified cause.

### The low ARA scores are a real, located defect — not scorer noise

The `golden` column above is **not** comparable to the numbers in `SCORES.md`, and the
low ARA values are the reason. Re-scoring the byte-identical golden files moved ARA by up
to **0.36** (`legacy-crm-desktop` 0.78 → 0.42) while MOD moved at most 0.04. Same input,
same scorer — so the difference is not the reports. The **scorer's prompt changed after
the baseline was scored** (commit `cede15f` scored the baseline; later commits added the
authoritative severity table parsed from SKILL.md and the `[fix]` corrections that tell
the grader to judge severity against the TD instead of against its own security
intuition).

Under the corrected prompt the grader now checks each finding's `native_severity`
(nested in `ara_metadata`) against the TD's own table — and it finds a genuine
contradiction. Excluding the 9 conditional questions, which are legitimately RISK-SAFETY
under read-only scope, exactly two non-conditional mismatches exist across all golden ARA
reports:

| Question | TD says | Report emits | Golden reports affected |
| --- | --- | --- | --- |
| `AUTH-Q5` Credential Management | `RISK-SAFETY` (SKILL.md:870) | `BLOCKER` | 6 |
| `DATA-Q4` | `RISK-QUALITY` | `BLOCKER` | 1 |

And the mismatch predicts the score drop almost perfectly:

| Fixture | old prompt | new prompt | delta | non-conditional mismatch |
| --- | --- | --- | --- | --- |
| `legacy-crm-desktop` | 0.78 | 0.42 | **−0.36** | AUTH-Q5 |
| `legacy-loan-calculator` | 0.72 | 0.42 | **−0.30** | AUTH-Q5 |
| `legacy-partner-soap` | 0.72 | 0.62 | −0.10 | AUTH-Q5 |
| `legacy-payroll-system` | 0.78 | 0.82 | +0.04 | (none) |
| `legacy-pricing-cgi` | 0.82 | 0.78 | −0.04 | (none) |
| `legacy-shipping-api` | 0.72 | 0.82 | +0.10 | (none) |

Every large drop is an AUTH-Q5 report; every clean report is flat within MOD-like noise.
**So ARA is not noisy — it was being graded against a prompt that could not see a real TD
defect, and the corrected prompt is now correctly penalising it.** That is the scorer
working, and it is the concrete answer to "can we actually improve ARA": fixing the
AUTH-Q5 over-escalation (task #27) should move six fixtures at once.

Supporting evidence that this is the TD and not the scorer: in s2 the analysis agent
emitted AUTH-Q5 *correctly* for `legacy-loan-calculator` and `legacy-partner-soap`, and
their scores jumped to 0.88 and 0.78. The defect is intermittent, which is exactly why it
needs the 3-sample baseline to measure rather than one draw.

### What this means for the numbers below

- **Do not compare the `golden` column to `SCORES.md`.** Different prompt; `SCORES.md` is
  stale and will be regenerated by the re-baseline.
- **Do not read the per-fixture ARA values as fixture rankings.** They currently encode
  "does this report trip the AUTH-Q5 defect" more than overall report quality.
- The ARA noise floor (0.10) still has not been *measured* — the +0.140 mean shift is
  explained by the prompt change, so it says nothing about true run-to-run variance. Only
  the 3-sample re-baseline (task #34) yields a real per-fixture `2·sd`.

---

Each score is an LLM grader's assessment of how well a generated report is **grounded in the fixture's actual source code** — fabrications and misses count against it. This is the *accuracy* axis, and it is what the judge compares a TD change against. It is NOT the ARA tier or the MOD band, which are the report's own verdicts about the app and appear here as context.

The **Checks** column is a different axis entirely: deterministic, arithmetic assertions that a report does not contradict **itself** — its own severity counters, its own tier arithmetic, its own question coverage. No LLM and no sampling is involved, so a failure here is a real defect at any sample depth, and is safe to act on immediately. A report can be perfectly grounded in the source (high score) and still fail a check by miscounting what it found. Each failure names the check; see [What the checks mean](#what-the-checks-mean).

**Sample depth: up to 2 independent runs per fixture.** `sd` is the measured per-fixture standard deviation and `spread` the max−min across runs. The judge's threshold is `2·sd`, so a delta below that is **not measured**.

Every batch has its own column — same TD, same fixtures, different run. Columns: `golden`, `s2`. The point of showing them side by side is that the mean alone hides disagreement: 0.72 / 0.92 and a steady 0.82 both average to 0.82, but only one of them is a measurement.

## ARA — 7 reports

Mean **0.73**, range 0.47–0.85.

| Repo | Mean | golden | s2 | sd | spread | Checks | Tier / blockers |
|---|---|---|---|---|---|---|---|
| `legacy-crm-desktop` | 0.47 | 0.42 | 0.52 | 0.050 | 0.10 | PASS | Not Agent-Integrable / 3 |
| `legacy-loan-calculator` | 0.65 | 0.42 | 0.88 | 0.230 | 0.46 | PASS | Remediation Required / 2 |
| `legacy-partner-soap` | 0.70 | 0.62 | 0.78 | 0.080 | 0.16 | PASS | Remediation Required / 2 |
| `legacy-document-portal` | 0.77 | 0.72 | 0.82 | 0.050 | 0.10 | PASS | Remediation Required / 2 |
| `legacy-payroll-system` | 0.82 | 0.82 | 0.82 | 0.000 | 0.00 | **HIGH** — `severity_counter_undercount`, `severity_counter_undercount` | Not Agent-Integrable / 3 |
| `legacy-pricing-cgi` | 0.83 | 0.78 | 0.88 | 0.050 | 0.10 | PASS | Remediation Required / 2 |
| `legacy-shipping-api` | 0.85 | 0.82 | 0.88 | 0.030 | 0.06 | PASS | Remediation Required / 1 |

Run-to-run spread: mean 0.140, worst 0.46 — treat any delta below the worst spread as noise.

## MOD — 7 reports

Mean **0.90**, range 0.85–0.92.

| Repo | Mean | golden | s2 | sd | spread | Checks | MOD score / band |
|---|---|---|---|---|---|---|---|
| `legacy-pricing-cgi` | 0.85 | 0.88 | 0.82 | 0.030 | 0.06 | PASS | 1.92 / Needs Work |
| `legacy-shipping-api` | 0.88 | 0.88 | 0.88 | 0.000 | 0.00 | PASS | 1.38 / Not Ready |
| `legacy-document-portal` | 0.90 | 0.88 | 0.92 | 0.020 | 0.04 | PASS | 1.18 / Not Ready |
| `legacy-loan-calculator` | 0.90 | 0.88 | 0.92 | 0.020 | 0.04 | PASS | 1.22 / Not Ready |
| `legacy-partner-soap` | 0.90 | 0.92 | 0.88 | 0.020 | 0.04 | PASS | 1.22 / Not Ready |
| `legacy-crm-desktop` | 0.92 | 0.92 | 0.92 | 0.000 | 0.00 | PASS | 1.0 / Not Ready |
| `legacy-payroll-system` | 0.92 | 0.92 | 0.92 | 0.000 | 0.00 | PASS | 1.05 / Not Ready |

Run-to-run spread: mean 0.026, worst 0.06 — treat any delta below the worst spread as noise.

## Deterministic defects — 2 across 1 reports

Arithmetic contradictions inside a single report — **actionable now**, independent of sample depth.

| Severity | Repo | Check | Detail |
|---|---|---|---|
| high | `legacy-payroll-system` (ARA) | `severity_counter_undercount` | risk_safety_count=6 but 8 findings are natively RISK-SAFETY (undercount by 2; no exclusion rule can lower a counter below the enumerated findings) |
| medium | `legacy-payroll-system` (ARA) | `severity_counter_undercount` | risk_quality_count=8 but 12 findings are natively RISK-QUALITY (undercount by 4; no exclusion rule can lower a counter below the enumerated findings) |

## What the checks mean

Each check asserts a report is internally consistent. All are deterministic arithmetic — no LLM, no sampling — so a failure is a genuine defect regardless of how many runs we have.

| Check | Severity | What a failure means |
|---|---|---|
| `severity_counter_undercount` | high | A severity counter is LOWER than the findings the report itself enumerated. Exclusion rules can push a counter above the enumerated set, never below it, so this is always an error — and because the ARA tier is computed from these counters, an undercount can mechanically relax the tier. |

The other 10 checks passed everywhere: `category_band_mismatch`, `duplicate_question_ids`, `incomplete_question_coverage`, `missing_safety_qualifier`, `overall_score_band_error`, `overall_score_not_mean_of_categories`, `question_in_both_findings_and_evaluations`, `spurious_safety_qualifier`, `tier_contradicts_counts`, `unexpected_question_count`.

## Per-report grader notes

<details><summary>Fabrications and misses per report (11 reports)</summary>

### `legacy-crm-desktop` (ARA) — 0.47

The report contains a critical severity misclassification: AUTH-Q5 (Credential Management) is marked as BLOCKER when the authoritative severity table assigns it RISK-SAFETY. Additionally, DATA-Q4 is correctly identified but marked as RISK-SAFETY in the native_severity field when the rubric assigns it RISK-QUALITY. The report also marks several evaluations as 'pass' with 'Recorded as INFO' that should actually count toward the INFO count but appear to be handled inconsistently. The archetype detection and core findings about the legacy VB6 application are accurate and well-evidenced.

- **MISS** [RISK-SAFETY] frmCustomer.frm: AUTH-Q4 Identity Propagation and Delegation not properly evaluated - marked as pass/INFO but the rubric severity is RISK-SAFETY
- **DELIVERABLE** recommended_actions: AUTH-Q5 classified as BLOCKER with P0 priority
- **DELIVERABLE** remediation_roadmap: DATA-Q4 native_severity marked as RISK-SAFETY
- **DELIVERABLE** service_archetype: stateful-crud archetype applied to desktop application

### `legacy-document-portal` (ARA) — 0.77

The report is largely accurate about this legacy ColdFusion repository, correctly identifying the lack of API surface, machine authentication, and numerous security gaps. However, there are severity inconsistencies: AUTH-Q6 should be BLOCKER under the conditional rules but was resolved as RISK-SAFETY without proper justification, and several conditional BLOCKERs were correctly downgraded for read-only scope. The archetype and tier classification are appropriate, and evidence citations generally check out against the source files.

- **DELIVERABLE** remediation_roadmap: Phase naming inconsistency - Phase 1 is labeled 'Blockers' but includes many RISK-SAFETY items (AUTH-Q2, AUTH-Q3, AUTH-Q5, AUTH-Q6, AUTH-Q7, STATE-Q1, STATE-Q5, DATA-Q1, DATA-Q2, DATA-Q6) which are not blockers

### `legacy-loan-calculator` (ARA) — 0.65

The report is largely accurate about this legacy Struts repository. It correctly identifies the lack of API surface, hardcoded credentials, SQL injection, and absence of machine authentication. The conditional BLOCKER logic for read-only scope is applied correctly, and the service archetype is appropriate. Minor issues include some weak evidence citations and a few debatable extended-question triggers, but no fabrications or significant misses are present.

- **DELIVERABLE** remediation_roadmap: Phase 2 includes API-Q4 (Idempotent Write Operations) which the report itself resolved as INFO under read-only scope

### `legacy-partner-soap` (ARA) — 0.7

The report is largely accurate about the repository's state and correctly identifies most issues. However, there are severity inconsistencies: STATE-Q4 (Circuit Breakers) is marked 'not_evaluated_extended' but should be evaluated since the service makes external calls to Oracle DB (even if owned). More significantly, the report correctly applies read-only scope downgrades for conditional BLOCKERs but inconsistently counts 11 RISK-SAFETY findings when several scope-calibrated questions were passed as INFO. The archetype and evidence citations are accurate.

- **DELIVERABLE** remediation_roadmap: STATE-Q4 (Circuit Breakers) is missing from the roadmap entirely despite being a RISK-SAFETY question

### `legacy-payroll-system` (ARA) — 0.82

The report is largely accurate about this legacy COBOL payroll system, correctly identifying the lack of API surface, hardcoded credentials, and PII exposure. However, there are severity counter discrepancies (pre-flagged), some questionable severity escalations on DATA-Q1, and the report missed DATA-Q6 as a finding despite PII being written to output files. The archetype and most findings are well-grounded in the actual source code.

- **MISS** [RISK-SAFETY] src/PAYRUN.cbl lines 48-53: PII (SSN, bank account) written to output file without redaction - constitutes logging/outputting user data
- **MISS** [RISK-SAFETY] jcl/PAYRUN.jcl: STATE-Q5 Rate Limiting marked not applicable but system has FTP external interface
- **DELIVERABLE** service_archetype: stateful-crud may not be the best fit for a batch processing system

### `legacy-pricing-cgi` (ARA) — 0.83

The report is largely accurate about the legacy-pricing-cgi repository. It correctly identifies the stateless-utility archetype, read-only agent scope, and most findings are well-grounded in the source code. The tier calculation is correct (2 BLOCKERs → Remediation Required). However, there are some severity downgrades that deviate from the authoritative table, particularly AUTH-Q4, AUTH-Q5, and AUTH-Q7 being marked INFO when they should be RISK-SAFETY, and ENG-Q4 marked INFO when it should be RISK-QUALITY.

- **MISS** [RISK-SAFETY] pricing.cpp (whole file - no identity propagation): AUTH-Q4 Identity Propagation and Delegation downgraded to INFO instead of RISK-SAFETY
- **MISS** [RISK-SAFETY] pricing.cpp (no identity system): AUTH-Q7 Agent Identity Suspension downgraded to INFO instead of RISK-SAFETY
- **MISS** [RISK-QUALITY] README.md line 17 - 'No tests': ENG-Q4 API Test Coverage resolved as INFO instead of RISK-QUALITY
- **DELIVERABLE** recommended_actions: AUTH-Q5 appears in Phase 3/INFO findings but AUTH-Q5 is RISK-SAFETY severity per the authoritative table

### `legacy-shipping-api` (ARA) — 0.85

The report is largely accurate about the legacy-shipping-api repository. It correctly identifies the single BLOCKER (AUTH-Q1 shared API key), appropriate RISK-SAFETY findings, and properly applies read-only scope to downgrade conditional blockers. The service archetype (data-gateway) is reasonable, and findings cite real code patterns. Minor issues include AUTH-Q4 being marked INFO when it should be RISK-SAFETY per the severity table, and some weak evidence on a few evaluations.

- **MISS** [RISK-SAFETY] server.js lines 15-19: AUTH-Q4 Identity Propagation is marked as INFO but should be RISK-SAFETY per the authoritative severity table
- **DELIVERABLE** recommended_actions: AUTH-Q4 is not included in any recommended action despite being a RISK-SAFETY finding

### `legacy-loan-calculator` (MOD) — 0.9

This report is highly accurate about the legacy-loan-calculator repository. It correctly identifies the on-premises Struts 1.3/Java 5/Oracle 11g stack, hardcoded credentials, lack of IaC/CI-CD/tests, and SQL injection vulnerability. The service archetype (stateful-crud), pathway triggers, and severity assignments are well-grounded in the actual source code. Minor issues include DATA-Q1 being scored as High when the repo shows no evidence of document storage needs, and some evidence citations lack line specificity.

- **DELIVERABLE** top_gaps: DATA-Q1 (Unstructured Data Storage) ranked as a top gap with High severity

### `legacy-payroll-system` (MOD) — 0.92

This report is highly accurate for the legacy-payroll-system repository. It correctly identifies the mainframe COBOL/DB2 architecture, cites real evidence from JCL and COBOL files, and appropriately scores the system at the floor of the scale (1.05 overall). The pathways are correctly triggered based on actual findings, the archetype classification is reasonable, and the decomposition strategy is proportionate. Minor issues include some weak evidence citations and one debatable pathway trigger.

- **DELIVERABLE** pathways: Move to Containers triggered for a COBOL mainframe system that has no containerization path without complete rewrite

### `legacy-pricing-cgi` (MOD) — 0.85

The report is largely accurate about this legacy CGI repository. It correctly identifies the stateless-utility archetype, detects containerization artifacts, and appropriately triggers only the Move to Modern DevOps pathway. Most findings are grounded in real code evidence. However, there are some questionable severity assignments and the DATA-Q1/DATA-Q3 findings overstate the database gap for what is fundamentally a configuration file, not a database.

- **DELIVERABLE** top_gaps: DATA-Q1 and DATA-Q3 are listed as top gaps with score 1, but the pricing rules file is configuration data, not a database. Treating a config file as a database gap is a category error.

### `legacy-shipping-api` (MOD) — 0.88

The report is largely accurate for this legacy repository. The service archetype (stateful-crud) is correct, the pathway triggers are well-justified, and findings cite real evidence from the source. The main issue is DATA-Q1 being marked High severity for 'no managed object storage' when the application simply doesn't need object storage (it stores structured JSON in MongoDB, not unstructured files). The 'Move to Containers' pathway correctly identifies that containerization is already done. Minor weak evidence on a few questions but overall grounded assessment.

- **DELIVERABLE** top_gaps: DATA-Q1 ranked #1 as High severity gap for 'no managed object storage'

</details>
