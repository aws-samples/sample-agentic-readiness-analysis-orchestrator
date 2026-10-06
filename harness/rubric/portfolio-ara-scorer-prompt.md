# Portfolio ARA Report Scorer — Self-Contained Grading Prompt

> **What this is.** The complete, self-contained prompt used to score a **Portfolio Agentic
> Readiness Analysis (Portfolio ARA)** report for *aggregation accuracy* — does the portfolio
> report accurately aggregate and represent the underlying per-repo ARA reports? It emits a
> single 0.0–1.0 accuracy score in the `<score>X.X</score>` format the benchmarking platform
> parses, plus a one-paragraph summary.
>
> **One prompt, one output.** This is a SINGLE prompt (no separate system/user split) and it
> emits ONLY `<score>X.X</score>` followed by a brief summary, and nothing else.
>
> **Self-contained** means every authoritative rule the grader needs (the portfolio TD's entry
> criteria, cross-cutting thresholds, program trigger conditions, portfolio-level questions,
> and the readiness-distribution arithmetic) is **baked in as literal text below** — the grader
> does NOT read `SKILL.md` or any TD reference file at runtime.
>
> **How to run it at scale.** Send the `## PROMPT` block as a single message with the three
> `{{...}}` placeholders filled in: `{{PORTFOLIO_NAME}}`, `{{REPOSITORY_SOURCE}}` (the complete
> source tree including all per-repo report JSONs), and `{{REPORT_JSON}}` (the generated
> portfolio ARA report, pretty-printed JSON).
>
> **Filling the placeholders — the REQUIRED inputs.** This is an *aggregation accuracy* check:
> the grader verifies every portfolio claim against the actual per-repo ARA report JSONs that
> the portfolio TD consumed as input. The scorer therefore needs:
>
> - **`{{REPOSITORY_SOURCE}}`** = the FULL source tree containing per-repo ARA report JSONs.
>   These live at `services/{repo-name}/agentic-readiness-analysis/{repo-name}-ara-report.json`.
>   The grader reads these to verify the portfolio report's claims about each repo's tier,
>   blocker count, and cross-cutting findings.
> - **`{{REPORT_JSON}}`** = the portfolio ARA report — the file matching
>   `*-portfolio-ara-report.json`. Locate it by globbing: `**/*-portfolio-ara-report.json`.
>
> **Fail loudly.** If the per-repo ARA reports or the portfolio report JSON is missing, error
> out — a missing input means the run was not scorable.

---

## PROMPT

````
You are a strict evaluator of automated portfolio-level code-assessment reports.

You are given (a) a source tree containing multiple repositories with their individual Agentic
Readiness Analysis (ARA) report JSONs, and (b) a generated Portfolio ARA report that aggregates
those individual reports. Judge whether the portfolio report ACCURATELY REPRESENTS the
aggregation of the underlying per-repo reports, then return a single accuracy score.

This is an AGGREGATION ACCURACY evaluation. The portfolio report consumes per-repo ARA report
JSONs and must faithfully represent their collective findings. Verify claims against the actual
per-repo reports:
  * A cross-cutting finding claiming a blocker appears in repos where it does not is a FABRICATION.
  * A blocker appearing in 2+ per-repo reports but absent from cross-cutting analysis is a MISS.
  * A readiness distribution contradicting actual per-repo tiers is a HARD FAILURE.
  * Program recommendations not grounded in actual portfolio-wide patterns are UNSUPPORTED.

YOU ARE GRADING AGGREGATION FIDELITY, NOT RE-ASSESSING THE REPOS. The per-repo reports are
treated as ground truth — the portfolio report's job is to accurately summarize, cross-reference,
and aggregate them. Three consequences:
  1. A per-repo report's tier/findings are CORRECT inputs even if you disagree with them.
  2. A portfolio claim supported by the per-repo data is CORRECT even if you'd aggregate differently.
  3. The portfolio cannot "discover" new per-repo findings — only aggregate what exists.

## What to check, in priority order

### 1. Readiness Distribution (HARD ARITHMETIC — DETERMINISTIC)

The portfolio reports a readiness distribution (count of repos per tier). Verify:
- Each repo's assigned tier matches its per-repo `classification.readiness_profile`
- The distribution sums to the total number of consumed reports
- The `services_analyzed` count in metadata matches actual consumed reports

A distribution that contradicts the per-repo tiers is a hard failure regardless of everything else.

### 2. Cross-Cutting BLOCKERs

A cross-cutting BLOCKER requires the SAME `question_id` to appear as a BLOCKER-severity finding
in **≥2** per-repo reports. Verify:
- Each reported cross-cutting blocker actually appears in ≥2 repos (check question_id + severity)
- No blocker appearing in ≥2 repos is missing from the cross-cutting list
- The repo list cited for each cross-cutting blocker is accurate

### 3. Cross-Cutting RISKs

The threshold for cross-cutting RISKs is: **max(3, 33% of applicable repos)** (rounded up).
Verify:
- RISK-SAFETY findings meeting the threshold are reported
- RISK-QUALITY findings meeting the threshold are reported (separately from RISK-SAFETY)
- Findings below threshold are NOT promoted to cross-cutting status

### 4. Service-by-Service Summary

Verify each service entry's:
- `readiness_profile` matches the per-repo report
- `blocker_count` matches the per-repo report's actual BLOCKER findings count
- `risk_safety_count` matches the per-repo report

### 5. Program Recommendations — JUDGE WHETHER THE SELECTION MADE SENSE

‼ **THE FULL CANDIDATE SET IS BELOW — ALL 39 PROGRAMS, BAKED IN.** This prompt is
self-contained by contract: the grader does not read `SKILL.md` or any TD reference file at runtime,
so the programs have to be here rather than pointed at.

‼ **AND THAT IS A FIX, NOT A CONVENIENCE.** This section used to list THREE programs with their
triggers and instruct that "a program recommended without its trigger being met is a defect". The
library holds 39. So a portfolio TD correctly recommending any of the other 36 met a grader with no
trigger to check it against, and by that rule had to be marked a defect — it penalised the right
answer. Our own committed portfolio golden recommends four programs and the prompt knew one of them.

Each row's "surface when" is the FIRST condition from the library's `Signal patterns` — enough to
decide whether a recommendation is grounded. Note the library's richer fields (`How to evaluate`,
`DO NOT recommend when`, `Prerequisite`) are NOT reproduced here: `How to evaluate` exists on only 3
of 39 entries, and the rest would triple this prompt's length. Where a row's condition is
insufficient to judge, say the evidence is inconclusive rather than assuming a defect.

| Program | Tag | Status | Surface when (first condition) |
|---|---|---|---|
| AI DLC (AI Driven Development Lifecycle) | `[ARA-anchor]` | Active | Portfolio shows teams without established AI-assisted development practices, or engineering-maturity findings indicate manual development workflows th |
| AXE (Agent Experience Engagement) | `[ARA-anchor]` | Active | Portfolio shows 3+ services in `Pilot-Ready` or `Agent-Ready` state, or business has defined customer/employee experience goals but lacks a technical |
| Innovation EBA (AIML-GenAI) | `[ARA-anchor]` | Active | Portfolio `context` indicates AI/ML or GenAI is a strategic imperative, executive sponsorship exists, use cases deliver critical business value, a dat |
| OLA (Optimization & Licensing Assessment) | `[MOD]` | Active | MOD findings indicate on-prem workloads needing migration; |
| OLA for Databases | `[MOD]` | Active | MOD `Move to Managed Databases` pathway triggered; |
| OLA for VMware | `[MOD]` | Active | VMware infrastructure detected in portfolio `context`; |
| DBC (Directional Business Case) | `[MOD]` | Active | MOD `Move to Managed Databases` pathway detected; |
| DBOLA (Database Optimization & Licensing Assessment) | `[MOD]` | Active | MOD `Move to Managed Databases` pathway with Oracle or SQL Server detected; |
| Migration Evaluator | `[MOD]` | Active | Early-stage; |
| Well-Architected Review | `[ARA+MOD]` | Active | ARA `Engineering Maturity` or `Observability` dimensions have 2+ `Medium`/`High` findings; |
| AI Assessment | `[ARA]` | Active | ARA shows `Pilot-Ready` or `Agent-Ready`; |
| MAP (Migration Acceleration Program) | `[ARA+MOD]` | Active | 3+ High-severity findings across any ARA dimension; |
| MAP for AI Modernization | `[ARA+MOD]` | Active | ARA profile is `Remediation Required` or `Pilot-Ready` AND customer has a modernization need to enable agentic/AI workloads; |
| AppMod PoC Funding | `[MOD]` | Active | MOD pathway detected (`Move to Containers` or `Move to Cloud Native`) and customer wants to validate approach on a specific application before scaling |
| Microsoft Modernization Program | `[MOD]` | Active | MOD findings reference Windows Server, .NET Framework, IIS, SQL Server; |
| VMware Modernization Program | `[MOD]` | Active | Large VMware estate detected in portfolio `context`; |
| AWS Modernization Assurance (AMA) | `[MOD]` | Active | Large VMware estate (2000+ VMs) referenced in `context`; |
| AWS-Funded ISV Tooling | `[MOD]` | Active | MOD findings show complex migration/modernization scope where specialized third-party tools would accelerate execution; |
| AWS Activate (Startup Credits) | `[ARA+MOD]` | Active | Customer is an early-stage startup (pre-Series B); |
| IW (Incremental Workloads) Programs for Startups | `[ARA+MOD]` | Active | Startup customer with findings indicating migration from competitive platform, or needing AI/ML assessment, or adopting new AWS services strategically |
| Activate4GF (Greenfield Credits) | `[ARA+MOD]` | Active | Customer is new to AWS (greenfield); |
| EBA (Experience-Based Acceleration) | `[ARA+MOD]` | Active | Multiple `High` effort remediation items in findings; |
| AML (Application Modernization Lab) | `[MOD]` | Active | MOD `Move to Containers` or `Move to Cloud Native` pathway + customer team needs both training and guided execution on modernization techniques. |
| Agentic Catalyst Program (ACP) | `[ARA]` | Active | ARA shows `Pilot-Ready` or `Agent-Ready`; |
| Immersion Days | `[ARA+MOD]` | Active | ARA findings show specific technology skill gaps (containers, serverless, observability); |
| GenAI Innovation Center | `[ARA]` | Active | ARA shows `Agent-Ready`; |
| ProServe Residency | `[ARA+MOD]` | Active | ARA shows `Remediation Required` with 10+ `High`/`Medium` findings spanning most dimensions; |
| AgentStorming Workshop | `[ARA]` | Active | ARA report generated but customer wants to identify WHERE to deploy agents across their business processes (beyond code-level readiness). |
| AWS AI League | `[ARA]` | Active | ARA `Engineering Maturity` dimension has 2+ `Medium`/`High` findings indicating team skill gaps in AI/agent development; |
| MMA Workshop (Migration and Modernization Acceleration) | `[MOD]` | Active | MOD `Move to Managed Databases` pathway with SQL Server, Oracle, or Sybase detected; |
| SHIP (Security Health Improvement Program) | `[ARA+MOD]` | Active | ARA findings reference hardcoded credentials, missing secrets management, no CloudTrail/audit trail, unmonitored network exposure, missing encryption, |
| AI Security Review | `[ARA+MOD]` | Active | A per-repo report in the portfolio evidences an AI or agent workload — its `findings[]`, `evaluations[]` or `context` name Amazon Bedrock, Amazon Bedr |
| AWS Transform Custom (ARA/MODA) | `[ARA+MOD]` | Active | Customer has additional repositories not yet analyzed; |
| AWS Transform for Windows | `[MOD]` | Active | MOD findings reference Windows/.NET/IIS workloads; |
| AWS Transform for SQL Server | `[MOD]` | Active | MOD `Move to Managed Databases` pathway with SQL Server detected; |
| RDS for SQL Server Cost Assessment | `[MOD]` | Active | Customer considering SQL Server migration but unsure about costs; |
| AWS Connected Community | `[ARA+MOD]` | Active | Customer is SMB or startup; |
| AWS Skill Builder | `[ARA+MOD]` | Active | ARA `Engineering Maturity` dimension has findings indicating team skill gaps; |
| Public Workshop Catalog (Self-Paced) | `[ARA+MOD]` | Active | MOD findings show specific technology pathways; |

All 39 are `Active` as of 2026-09-28. A `Retiring` program must never be recommended, and a
`Pilot` one must carry its region/segment caveat — neither status is present today, so if you see one
the table is stale and that itself is worth reporting.

What to judge, in this order:

1. **Grounded** — for each recommended program, is its "surface when" condition in the table
   above actually met by the per-repo data? A program whose condition is demonstrably unmet is a
   defect. Where the row's condition is too coarse to decide, say the evidence is inconclusive rather
   than assuming a defect.
2. **Sensible** — would a practitioner reading this portfolio reach for these programs? A
   recommendation can be technically triggered and still be poor judgment: three overlapping
   programs where one would do, an anchor program for a portfolio with one repo, or a database
   program for a portfolio with no databases.
3. **Complete** — is an obviously-applicable program absent? A portfolio that plainly meets a
   trigger and recommends nothing is as wrong as one that over-recommends.
4. **Status-aware** — a `Retiring` program must never be recommended; a `Pilot` one must carry its
   region/segment caveat.

This dimension is **judgment, not arithmetic**. Say what a practitioner would have chosen and why
the report's selection is better, worse, or equivalent.

### 5b. Path Forward — JUDGE WHETHER THE RECOMMENDED SEQUENCE MADE SENSE

The portfolio report proposes an order of work: remediation guidance, phasing, and what to do first.
Nothing in this prompt previously scored it, so a report could sequence its recommendations
arbitrarily and still score 0.90+. Judge it:

1. **Grounded in the per-repo evidence** — does each step trace to findings that actually exist in
   the input reports? An unsupported step is a fabrication, the same defect class as a fabricated
   cross-cutting finding.
2. **Ordered defensibly** — do prerequisites precede the work that needs them? Cross-cutting
   BLOCKERs generally precede per-repo polish; a step that cannot start until another finishes must
   not be scheduled first.
3. **Proportionate** — does the effort implied match the portfolio's size and readiness spread? A
   four-phase programme for three healthy repos is as wrong as a single phase for twenty mixed ones.
4. **Honest about what it cannot know** — where the evidence does not support a recommendation, the
   report should say so rather than assert a sequence.

‼ **JUDGMENT DIMENSIONS ARE NOISIER THAN ARITHMETIC ONES, AND THAT IS EXPECTED HERE.** The analysis
being scored is itself LLM-generated, so there is no deterministic ground truth to diff against.
Read movement on 5 and 5b **categorically** — better, worse, or equivalent — and never as a numeric
regression. Portfolio rollups are already unstable run-to-run; do not compound that by treating a
0.02 shift on a judgment dimension as signal.

### 5c. Recommendation QUALITY — grade the deliverable, not just whether it fired

The per-category findings are the report's WORKING. `recommended_actions` and
`remediation_roadmap` are what a customer actually reads and acts on, so they carry real weight.
Use the same vocabulary as the per-repo scorer: **FABRICATION** (a claim the inputs contradict),
**MISS** (something the inputs plainly support, absent), **WEAK EVIDENCE** (prose that restates the
category without pointing at anything).

**`recommended_actions[]` — each entry carries `trigger_reason`, `status`, `suggested_timing`,
`duration`, `what_it_provides`.**

1. **Is `trigger_reason` arithmetically true?** It cites numbers — "61 Engineering Maturity findings
   across portfolio", "76 BLOCKERs across 15 services". Count them in the per-repo inputs. A cited
   figure that does not reconcile is a FABRICATION, not a rounding quibble.
2. **Does `status: "Triggered"` match its "surface when" condition** from the program table above?
3. **Do the `suggested_timing` values compose?** Two programs both saying "run first" is a
   sequencing defect. So is a prerequisite scheduled after the thing that needs it.
4. **Is the set non-redundant?** Four programs that overlap in `what_it_provides` is worse advice
   than two that do not. Say which you would drop.
5. **Is it proportionate?** A multi-week expert engagement recommended for three healthy services is
   as wrong as a single workshop for a portfolio with 76 BLOCKERs.

**`remediation_roadmap.items[]` — each carries `phase`, `category_question_id`, `native_severity`,
`safety_impact`, `common_finding_summary`, `root_cause_pattern`, `remediation`,
`remediation_detail`, `affected_repos_count`, `applicable_repos_count`, `affected_services[]`.**

6. **Arithmetic first, it is free.** `affected_repos_count` must equal `len(affected_services)`, and
   both must reconcile with the per-repo findings for that `category_question_id`. Any mismatch is a
   defect regardless of how good the prose is.
7. **`affected_repos_count` vs `applicable_repos_count` must support the claim.** A
   `root_cause_pattern` of "systematic absence across portfolio" needs affected ≈ applicable. 8 of
   15 is not systematic; 12 of 12 is.
8. ‼ **IS THE `remediation` A CONCRETE ACTION, OR THE CATEGORY NAME RESTATED?** This is the most
   common quality defect in portfolio output and it is invisible to arithmetic checks. A remediation
   reading "Implement documented api interface across affected services" for category "Documented
   API Interface" tells the customer nothing they did not already have — it is the question echoed
   back as an answer. That is **WEAK EVIDENCE**, and a roadmap where most items read that way should
   not score in the top band however correct its counts are. Check `remediation_detail`
   (`approach` / `immediate_action` / `target_state`) for whether real content lives there instead;
   if it does, say so rather than penalising twice.
9. **Phasing.** Every BLOCKER and every `safety_impact: true` item belongs in phase 1. A critical
   item sequenced behind a cosmetic one is a defect even when both items are individually correct.
10. **One root cause is ONE item.** Do not credit — or penalise — the same underlying defect once
    per `category_question_id` it touches.

Do not award credit for confident tone, thorough formatting, or plausible-sounding generic advice. A
portfolio report can be fluent, internally consistent, arithmetically perfect, and still give a
customer nothing they can act on.

### 6. Portfolio-Level Questions (PORT-ARA-Q1 through PORT-ARA-Q5)

These assess capabilities only visible across multiple repos:
- PORT-ARA-Q1: Shared Identity Fabric
- PORT-ARA-Q2: Centralized Secrets Management
- PORT-ARA-Q3: Portfolio-Wide Observability
- PORT-ARA-Q4: Cross-Service Authorization Model
- PORT-ARA-Q5: Agent Governance Framework

Verify these reference actual evidence from multiple per-repo reports (not fabricated claims).

### 7. Dependency Map

If `dependency_overrides` were provided in context, verify the dependency map reflects them.
If no overrides, verify the map is constructed from per-repo evidence (imports, service calls).

### 8. Metadata

- `consumed_per_repo_json_files` lists files that actually exist in the source tree
- `services_analyzed` count matches the consumed file count
- `analysis_date` and `td_version` are present

## Per-repo report location

Per-repo ARA reports are at:
```
services/{repo-name}/agentic-readiness-analysis/{repo-name}-ara-report.json
```
Match by glob: `**/*-ara-report.json` (excluding `*-portfolio-ara-report.json`)

## Scoring scale

Score how ACCURATELY the portfolio report aggregates its input reports:
  0.90-1.00  distribution matches, cross-cutting findings verified, programs grounded AND
             sensible, path forward defensible, metadata correct, no fabrications
  0.75-0.89  accurate overall; one minor threshold edge case, one debatable program rec, a
             cosmetic metadata discrepancy — OR a roadmap whose remediations mostly restate their
             category instead of naming a concrete action (see 5c.8), however correct the counts
  0.55-0.74  a real defect — wrong readiness count, fabricated cross-cutting finding, program
             triggered without meeting conditions, a `trigger_reason` figure that does not
             reconcile, `affected_repos_count` disagreeing with `affected_services[]`, or an
             arithmetic error in distribution
  0.30-0.54  multiple real defects, or a distribution that contradicts the per-repo data
  0.00-0.29  the portfolio report is substantially disconnected from its input reports

A report with correct distribution, verified cross-cutting findings, grounded programs, and
accurate metadata belongs at 0.90+.

‼ **A report can be arithmetically perfect and still not belong at 0.90+.** If the programs are all
triggered but the selection is poor judgment, the path forward is unordered or unsupported, or the
remediations restate their categories rather than naming concrete actions, cap it in the 0.75-0.89
band and say which of 5 / 5b / 5c cost it. **Arithmetic is necessary, not sufficient** — a customer
cannot act on a correct count.

## SOURCE TREE — {{PORTFOLIO_NAME}}
(contains per-repo ARA report JSONs — verify the portfolio's claims against these)
{{REPOSITORY_SOURCE}}

## GENERATED PORTFOLIO REPORT OUTPUT
{{REPORT_JSON}}

Now decide. Work through: (1) distribution accuracy, (2) cross-cutting blocker verification,
(3) cross-cutting risk threshold, (4) service summary accuracy, (5) program trigger validation,
(6) portfolio-level question grounding, (7) metadata checks. Then output EXACTLY a score tag
followed by a brief summary, and nothing else:

<score>X.X</score>
<one paragraph: is this portfolio report an accurate aggregation of its per-repo inputs? Name
concrete fabrications, miscounts, ungrounded programs, or threshold violations — or state that
none were found.>
````

---

## Maintenance

This prompt is pinned to the portfolio ARA TD's aggregation logic. When the portfolio TD changes
(cross-cutting thresholds, program triggers, portfolio-level questions), this prompt must be
updated to match. Unlike the per-repo prompts, there is no `scorer-prompt-sync.py` automation
for portfolio prompts yet — updates are manual.

| If you change… (in the portfolio ARA TD) | Update this section |
|---|---|
| Cross-cutting BLOCKER threshold (currently ≥2) | §2 Cross-Cutting BLOCKERs |
| Cross-cutting RISK threshold (max(3, 33%)) | §3 Cross-Cutting RISKs |
| Program trigger conditions | §5 Program Recommendations |
| Portfolio-level questions (PORT-ARA-Q1–Q5) | §6 Portfolio-Level Questions |
| Entry criteria (min reports) | Opening paragraph + §1 |
