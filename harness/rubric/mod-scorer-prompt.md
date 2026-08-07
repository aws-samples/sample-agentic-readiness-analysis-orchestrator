# MOD Report Scorer — Self-Contained Grading Prompt

> **What this is.** The complete, self-contained prompt used to score a **Modernization Readiness
> Analysis (MOD)** report for *groundedness* — is the report accurate about the repository it
> analyzed? It emits a single 0.0–1.0 accuracy score in the `<score>X.X</score>` format the
> benchmarking platform parses, plus a one-paragraph summary.
>
> **One prompt, one output.** This is a SINGLE prompt (no separate system/user split) and it
> emits ONLY `<score>X.X</score>` followed by a brief summary — nothing else to parse. The
> structured reasoning below (fabrications, misses, rubric gaps, deliverable defects) is *how the
> grader thinks its way to the score*, not a JSON object it must return. That is the difference
> from the harness's live grader, which returns a full JSON verdict for the harness to aggregate.
>
> **Self-contained** means every authoritative table the grader needs (the 37-question / 5-category
> rubric, the 1–4 scoring scale, the score→severity mapping, the core/non-core designation, the
> surface gates and archetype calibrations, the classification thresholds and score bands, and the
> 7 canonical pathways) is **baked in as literal text below** — the grader does NOT read `SKILL.md`
> or any TD reference file at runtime. That is the difference between this file and the harness's
> live `score-reports.py`, which parses those tables from the TD on every run. When the TD changes,
> **this file must be updated by hand** (see *Maintenance* at the bottom). It is pinned to the
> 37-question / 5-category MOD rubric.
>
> **How to run it at scale.** Send the `## PROMPT` block as a single message with the three
> `{{...}}` placeholders filled in: `{{REPO_NAME}}`, `{{REPOSITORY_SOURCE}}` (the complete repo
> source), and `{{REPORT_JSON}}` (the generated MOD report, pretty-printed JSON).
>
> **Where the report lives (fill `{{REPORT_JSON}}` from here).** Each MOD run emits a four-artifact
> bundle. Load the **JSON** artifact — it is the canonical machine-readable contract; the `.md`,
> `.html`, and `.metadata.json` siblings are NOT the grading input. On disk:
> ```
> {portfolio-or-repo}/services/{repo-name}/modernization-readiness-analysis/{repo-name}-mod-report.json
> ```
> `{repo-name}` is the config slug (lowercased, `[^a-z0-9_-]` → `-`), which may differ from the
> on-disk directory name. `{{REPOSITORY_SOURCE}}` is the analyzed repo's complete source — the same
> tree the report was generated against. If the JSON artifact is missing or unreadable, the run
> cannot be scored: fail loudly rather than grading against the `.md` or `.html`.

---

## PROMPT

````
You are a strict evaluator of automated code-assessment reports.

You are given (a) the COMPLETE source of a repository and (b) a generated Modernization Readiness
Analysis (MOD) report about that repository. Judge whether the report is ACCURATE ABOUT THAT
SOURCE, then return a single accuracy score.

This is a GROUNDEDNESS evaluation. You have the entire repository, so verify claims against it
rather than judging plausibility:
  * A finding citing a file, function, or pattern that does not exist is a FABRICATION.
  * A real, serious problem visible in the source but absent from the report is a MISS — and a
    missed High finding is the expensive error, weighted far above a spurious low-severity one.
  * Prose that restates a question without pointing at concrete evidence is WEAK EVIDENCE.

YOU ARE GRADING RUBRIC APPLICATION, NOT RE-DOING THE ASSESSMENT YOURSELF. The report was produced
by scoring a FIXED question set on a FIXED 1-4 scale, given to you below as the authoritative
question bank. Grade whether it applied that rubric correctly and grounded its scores in real
code. Three consequences, and they are the difference between a fair score and a harsh one:
  1. A question scored on its own 1-4 criteria, mapped to severity by the score→severity table,
     is CORRECT — even if you would personally have rated the underlying issue more harshly. That
     is not a miss.
  2. A real problem the rubric has NO question for is a RUBRIC GAP, not a report miss — the report
     cannot answer a question it was never asked.
  3. One root cause is ONE item. Do not count the same underlying defect once per question_id it
     touches.
Only count a MISS when a question the rubric DOES cover was left unscored, scored at a level the
source plainly contradicts (e.g. a "4 — fully managed" on code that has none of it), or whose
severity mapping is wrong for its core/non-core designation.

GRADE THE DELIVERABLES, NOT JUST THE QUESTION SCORES. The per-question scores are the report's
WORKING; the deliverables are what a customer acts on, so they carry real weight:
  * `overall_score` and per-category scores — is `overall_score` the equally-weighted mean of the
    5 category scores, and does each category score reflect its own question scores? An arithmetic
    inconsistency here is a defect.
  * `classification` — is the readiness classification consistent with the High/Medium finding
    counts per the classification table? A classification that contradicts its own counts is a
    hard failure.
  * `modernization_pathways` — are the emitted pathways triggered by conditions actually present
    in the source, and are their guards respected (a pathway fired whose guard should have
    suppressed it is a defect)? Are pathway IDs from the canonical set of 7?
  * `recommendations` / roadmap — does the phasing put the High-severity gaps first, and does each
    recommendation map to real question scores and concrete changes to THIS repo rather than
    generic cloud advice?
An unsupported or inconsistent deliverable is a defect on the same footing as a bad score.

Be skeptical and specific. Do not award credit for confident tone, thorough formatting, or
plausible-sounding generic advice.

Note the repositories are deliberately small legacy fixtures. Judge the report against what is
ACTUALLY THERE — do not penalise it for not finding problems the source does not contain, and do
not reward it for findings the source does not support. A legacy fixture landing at the bottom of
the scale is very often the CORRECT answer; scoring it that way is accuracy, not leniency.

WHAT TO CHECK, IN PRIORITY ORDER (NOTE: MOD questions are scored 1-4, where 1 = worst / legacy and
4 = best / cloud-native — NOT 0-4):
  * Score-to-severity consistency — each 1-4 score maps to the correct unified severity per the
    mapping below, accounting for whether the question is core or non-core.
  * Classification accuracy — the readiness classification (Cloud-Native Ready, Pilot-Ready,
    Remediation Required, Not Ready) is a DETERMINISTIC function of the High and Medium finding
    counts; a classification that contradicts the report's own counts is a hard failure.
  * Overall-score arithmetic — `overall_score` is the equally-weighted mean of the 5 category
    scores, and the score-band label matches it.
  * Evidence quality — each question cites specific files and code patterns.
  * Archetype and pathway accuracy — emitted pathways are triggered by conditions actually
    present, with guards respected, drawn from the 7 canonical pathway IDs.
  * Question coverage — all 37 questions across the 5 categories (Infrastructure 11, Application
    6, Data 4, Security 7, Operations 9) are scored, except surface-gated questions correctly
    marked N/A when their surface is absent.
Weight a missed High finding (a core question that should have scored 1, or a genuinely severe
non-core gap) far above a spurious Low. But a missed High means a question the source scores at
level 1 (core) that the report scored higher without support — NOT a finding you would personally
have rated more harshly. If the report scored the question against its own 1-4 criteria and the
source supports that score, it is CORRECT and is not a miss.

## Authoritative MOD question bank (the spec — 37 questions across 5 categories)

SCOPE BOUNDARY: MOD is a design-time modernization review. It scores whether cloud-native
practices are PRESENT in code and configuration on a 1-4 maturity scale. It is NOT a penetration
test, a runtime scan, or a CVE audit. Each question is scored by its own 1-4 criteria; severity
is then DERIVED from the score via the mapping below. "This is bad" is not by itself grounds for a
score of 1 — the 1-4 criteria decide.

INFRASTRUCTURE & DevOps (INF, 11):
  INF-Q1 Managed Compute, INF-Q2 Managed Databases, INF-Q3 Workflow Orchestration,
  INF-Q4 Async Messaging and Streaming, INF-Q5 Network Security, INF-Q6 API Entry Point,
  INF-Q7 Auto-Scaling, INF-Q8 Backup and Recovery, INF-Q9 High Availability and Fault
  Isolation, INF-Q10 Infrastructure as Code Coverage, INF-Q11 CI/CD Automation.
APPLICATION ARCHITECTURE (APP, 6):
  APP-Q1 Programming Languages, APP-Q2 Monolith vs Microservices, APP-Q3 Async vs Sync
  Communication, APP-Q4 Long-Running Process Handling, APP-Q5 API Versioning Strategy,
  APP-Q6 Service Discovery.
DATA PLATFORM (DATA, 4):
  DATA-Q1 Unstructured Data Storage, DATA-Q2 Unified Data Access Layer,
  DATA-Q3 Database Engine Version and EOL, DATA-Q4 Stored Procedures and Schema Complexity.
  (Note: MOD DATA-Q1..Q4 are DIFFERENT questions from ARA DATA-Q1..Q7 — do not conflate.)
SECURITY BASELINE (SEC, 7):
  SEC-Q1 Audit Logging, SEC-Q2 Encryption at Rest, SEC-Q3 API Authentication,
  SEC-Q4 Centralized Identity Integration, SEC-Q5 Secrets Management,
  SEC-Q6 Compute Hardening and Patching, SEC-Q7 Application Security Pipeline.
OPERATIONS & OBSERVABILITY (OPS, 9):
  OPS-Q1 Distributed Tracing, OPS-Q2 SLO Definitions, OPS-Q3 Business Metrics,
  OPS-Q4 Anomaly Detection and Alerting, OPS-Q5 Deployment Strategy,
  OPS-Q6 Integration Testing, OPS-Q7 Incident Response Automation,
  OPS-Q8 Observability Ownership, OPS-Q9 Resource Tagging Governance.

1-4 SCORING SCALE (uniform intent across questions):
  1 = legacy / absent — no cloud-native practice present
  2 = partial / ad-hoc — some practice, significant gaps
  3 = mostly modern — practice present with minor gaps
  4 = fully cloud-native / managed — best practice fully realized

SCORE -> UNIFIED SEVERITY MAPPING (depends on core/non-core designation):
  score 1, CORE question       -> High
  score 1, NON-CORE question   -> Medium
  score 2 (core or non-core)   -> Medium
  score 3 (core or non-core)   -> Low
  score 4 (core or non-core)   -> no finding emitted
A report applying this mapping is CORRECT. Do NOT re-derive severity from your own sense of how
serious the gap is — the score decides, and the score is set by the 1-4 criteria.

CORE QUESTION DESIGNATION (14 core — a score of 1 here is High):
  INF-Q1, INF-Q2, INF-Q5, INF-Q10, INF-Q11,  APP-Q2,  DATA-Q1, DATA-Q3, DATA-Q4,
  SEC-Q1, SEC-Q2, SEC-Q5,  OPS-Q5, OPS-Q6.
The remaining 23 questions are NON-CORE (a score of 1 maps to Medium, not High).

CLASSIFICATION (deterministic — a pure function of High and Medium finding counts):
  0 High AND <= 1 Medium            -> Cloud-Native Ready
  0 High AND >= 2 Medium            -> Pilot-Ready
  exactly 1 High                    -> Pilot-Ready
  2 to 11 High                      -> Remediation Required
  >= 12 High                        -> Not Ready
Low findings are classification-INERT — they never change the classification. The report must
ALSO emit a `classification_consistency_check` reconciling the classification with the counts; a
check that passes while the counts contradict the classification is itself a defect.

OVERALL SCORE AND BANDS:
  overall_score = equally-weighted mean of the 5 CATEGORY scores (each category score is the mean
  of its own answered questions). It is NOT weighted by question count.
  Band labels:  >= 3.5 Mature | 2.5-3.4 Partial | 1.5-2.4 Needs Work | < 1.5 Not Ready
A band label that does not match the numeric overall_score is a deliverable defect.

PER-CATEGORY THREE-LABEL EMISSION: each category emits a `numeric_score` (1-4 mean), a
`score_rating` (the band label for that mean), and a `severity_status` (rolled up from its
questions' findings). All three must be mutually consistent for the category.

## Per-report resolution — apply these against THIS report's metadata

The question bank above is the DEFAULT. Three mechanisms legitimately move a question off it for a
particular report. Read `metadata.service_archetype` and `metadata.surface_flags` (or the
equivalent surface fields), then apply the rules below BEFORE recording any miss or mis-score.

1. SURFACE GATES (question is N/A when its surface is absent). These questions are scored ONLY
   when the relevant surface exists. When the surface flag is `false` they are recorded "Not
   Evaluated (archetype-N/A)" and EXCLUDED from the category mean, the overall_score, and all
   finding counts. A question so marked because its surface is genuinely absent is CORRECT — even
   for a core question — and a FINDING emitted on such a question is itself a defect (the TD fails
   the analysis with an "N/A / Not Evaluated leak" error). The six surface flags are
   `has_persistent_data_store`, `has_at_rest_data_surface`, `has_deployed_workload`,
   `has_api_surface`, `has_multi_instance_deployment`, `has_iac_provisioning_aws_resources`.
   - INF-Q2 Managed Databases: Not Evaluated when `has_persistent_data_store == false` (no DB,
     managed or self-managed — a build tool / pure utility / frontend-only app).
   - SEC-Q1 Audit Logging: Not Evaluated UNLESS the repo contains account/foundation-level IaC
     (CloudTrail, AWS Config, GuardDuty, Org SCPs, centralized logging). Application-level IaC
     repos (single-service ECS/RDS/Lambda) are Not Evaluated — CloudTrail is an account-level
     concern.
   - SEC-Q2 Encryption at Rest: Not Evaluated when `has_at_rest_data_surface == false` (no DB, S3
     bucket, EBS/EFS, or similar managed storage; e.g. a library or CLI tool).
   - OPS-Q2 SLO Definitions: Not Evaluated when `has_api_surface == false` AND
     `has_persistent_data_store == false` (no user-facing surface SLOs are meaningful for).
   - OPS-Q5 Deployment Strategy: Not Evaluated when `has_deployed_workload == false` (no
     Dockerfile+manifests, no compute IaC, no deployment config — source-only repo whose deploy is
     managed in a separate GitOps/deployment-config repo).
   Do not import infrastructure expectations onto a pure library. Several of these ALSO carry a
   documented "external context dependency" — IaC/networking/SLO/deployment evidence often lives
   in a companion repo, so a score of 1 on INF-Q5, INF-Q10, SEC-Q1, OPS-Q2, or OPS-Q5 has a known
   false-positive rate; a report that scored 2 (not 1) citing that limitation, or that deferred to
   `additionalPlanContext`, is applying the TD correctly.

2. ARCHETYPE-KEYED RUBRICS (score criteria differ by archetype). EXACTLY FOUR questions are
   archetype-calibrated — INF-Q3, INF-Q4, APP-Q3, APP-Q4 — and only these four ever carry
   `mod_metadata.archetype_calibrated: true`. For them the 1-4 criteria are archetype-specific
   (columns for stateless-utility / data-gateway / stateful-crud / orchestrator / event-processor),
   so a score correct for one archetype would be wrong for another. When `repo_type` is not
   `application` (no archetype detected), the `stateful-crud` column is the default. Judge the
   score against the criteria for the report's `service_archetype`:
   - INF-Q3 Workflow Orchestration and INF-Q4 Async Messaging and Streaming: for a
     `stateless-utility`, "no multi-step workflows / synchronous is correct" records as Not
     Evaluated (archetype-N/A), NOT a default Score 4 and NOT a gap. A score of 1 for an
     `orchestrator` (no orchestration despite fan-out; synchronous-only fan-out across 3+ services)
     is the anti-pattern the rubric expects to be flagged.
   - APP-Q3 Async vs Sync Communication and APP-Q4 Long-Running Process Handling: for a
     `stateless-utility` where sync / short operations are the correct design, these record as Not
     Evaluated (archetype-N/A), not Score 4. A stateless-utility scoring high here is correct, not
     generous.
   When any of these four resolves to Not Evaluated (archetype-N/A) it is EXCLUDED from the
   category mean and overall_score. A score that correctly follows the archetype-keyed criteria —
   including a correct Not-Evaluated — is CORRECT and is not a miss. If `archetype_calibrated: true`
   appears on any question OTHER than these four, that is a defect.

3. PATHWAYS AND THEIR GUARDS (exactly 7 canonical IDs). Every MOD JSON emits a `pathways[]` array
   with EXACTLY 7 entries — one per canonical pathway, each with `status` ∈ {Triggered, Not
   Triggered, Not Applicable}. The canonical IDs (use these exact strings — a pathway ID outside
   this set is a defect):
     1. move-to-cloud-native   2. move-to-containers   3. move-to-open-source
     4. move-to-managed-databases   5. move-to-managed-analytics   6. move-to-modern-devops
     7. move-to-ai
   A pathway uses a Primary + Supporting model: it is `Triggered` ONLY when its Primary condition
   is met (Supporting conditions strengthen the case but never trigger alone). Surface-gating (§1)
   is applied BEFORE pathway evaluation — a question recorded Not Evaluated does NOT count toward
   triggering. A `triggering_questions[]` entry must be a `(question_id, score)` tuple whose
   question_id is in the pathway's trigger set and whose score < 3. Judge each emitted pathway
   against its Primary trigger and Contextual Guard:
   - move-to-cloud-native   — Primary: APP-Q2 < 3. Supporting: any of INF-Q1<3, APP-Q3<3, APP-Q4<3.
   - move-to-containers     — Primary: INF-Q1 < 3 AND no container definitions found.
                              GUARD: SHALL NOT trigger if compute is already Lambda/Fargate/ECS.
   - move-to-open-source    — Primary: DATA-Q4 < 3. Supporting: commercial DB engines in INF-Q2.
   - move-to-managed-databases — Primary: INF-Q2 < 3. Supporting: DATA-Q3 < 3.
   - move-to-managed-analytics — Primary: INF-Q4 < 3. GUARD: evidence of data-processing
                              workloads must exist.
   - move-to-modern-devops  — Primary: INF-Q10 < 3 OR INF-Q11 < 3. Supporting: OPS-Q5<3, OPS-Q6<3.
   - move-to-ai             — Primary: no AI/agent frameworks, no vector DB, no RAG, no agent-eval
                              framework. GUARD: requires AI/agent/LLM intent in the portfolio or
                              service context — a move-to-ai fired on an incidental keyword with no
                              real AI intent is a defect.
   A pathway fired against a failing guard, on an N/A-gated question, or on a Supporting-only
   signal with no Primary is a deliverable defect. A pathway correctly Not Triggered (threshold met
   or guard blocked) or Not Applicable (wrong repo_type — e.g. move-to-containers for a library) is
   NOT a miss.
   Plus one conditional deliverable the TD layers on top — DECOMPOSITION STRATEGY: a structured
   `decomposition_strategy` object (else `null`) emitted when APP-Q2 < 3 (a monolith with a
   decomposable seam), withheld at APP-Q2 >= 3.

## Scoring scale

Score how ACCURATE the report is, not how un-modern the repo is:
  0.90-1.00  no fabrications, no covered-question misses, sound deliverables, scores check out
  0.75-0.89  accurate overall; minor weak evidence, one debatable score, or a cosmetic
             deliverable flaw
  0.55-0.74  a real defect — a covered question mis-scored against the source, a wrong
             classification, a wrong overall_score arithmetic, or a pathway fired against its guard
  0.30-0.54  multiple real defects, or a fabrication that changes the conclusion
  0.00-0.29  the report is substantially wrong about this repository
A report with no fabrications, no covered-question misses, and no deliverable defects after
applying the resolution rules belongs at 0.90+.

## COMPLETE REPOSITORY SOURCE — {{REPO_NAME}}
(this is the entire repository; verify the report's claims against it)
{{REPOSITORY_SOURCE}}

## GENERATED REPORT OUTPUT
{{REPORT_JSON}}

Now decide. Work through fabrications, covered-question misses (each owned by a rubric question_id
— if none owns it, it is a rubric gap, not a miss), deliverable defects, and weak evidence,
applying the per-report resolutions above. Then output EXACTLY a score tag followed by a brief
summary, and nothing else:

<score>X.X</score>
<one paragraph: is this report accurate about this repo? Name the concrete fabrications, misses
(with their question_ids), or deliverable defects that drove the score — or state that none were
found.>
````

---

## Maintenance

This prompt is **pinned by hand** to the MOD rubric as of the split-managed-tds-modular branch
(37 questions, 5 categories, 1–4 scale). The live harness (`harness/score-reports.py`) derives the
same tables from the TD at runtime and will drift from this file the moment a score criterion,
core designation, surface gate, archetype rubric, classification threshold, score band, or pathway
changes in `definitions/managed/modernization-readiness-analysis/`. When you edit the TD, update
the corresponding block here:

| If you change… (in the MOD TD) | Update this section |
|---|---|
| A question's 1-4 criteria or the category counts | *Authoritative MOD question bank* |
| The score → severity mapping | *Score → unified severity mapping* |
| Which questions are core | *Core question designation* |
| A surface gate | *Per-report §1* |
| An archetype-keyed rubric | *Per-report §2* |
| A pathway ID, trigger, or guard (incl. decomposition / move-to-ai) | *Per-report §3* |
| The classification thresholds | *Classification* |
| The overall-score formula or band labels | *Overall score and bands* |

The scoring policy (the scale, "one root cause = one item", "a score disagreement is not a miss")
is judging policy, not TD fact — keep it stable unless you are deliberately re-tuning the grader.
