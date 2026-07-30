# s1 vs s2 — accuracy side by side (INTERIM)

> **This is NOT the committed baseline.** It is an ad-hoc, *partial* comparison of two
> independent analysis runs, kept so the s1/s2 difference is reviewable while s3 is still
> generating. The committed record stays [`SCORES.md`](./SCORES.md) /
> [`golden-accuracy-baseline.json`](./golden-accuracy-baseline.json) — neither was touched
> to produce this file (no `--update-baseline`).
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
fixtures improved and none regressed, with a mean shift of +0.140 that is larger than the
0.10 ARA noise floor the judge currently uses. A symmetric noise process does not produce
6-0.

Two readings, and this data cannot separate them at n=2:
1. **The ARA noise floor is too low.** A 0.46 single-fixture swing means the floor should
   be nearer the observed spread than 0.10 — in which case the judge is currently calling
   real noise a "measured regression".
2. **The s1 golden ARA reports are simply worse** (they were generated earlier), and s2 is
   the more representative draw — in which case the *baseline* is what needs replacing.

Either way the conclusion is the same and it is the reason task #34 exists: **a
single-draw ARA baseline cannot support the deltas the judge reasons about.** Do not read
the per-fixture ARA numbers below as fixture rankings. s3 resolves this — with three
samples the threshold becomes real per-fixture `2·sd` instead of a fixed floor.

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
