# ARA Report Scorer — Self-Contained Grading Prompt

> **What this is.** The complete, self-contained prompt used to score an **Agentic Readiness
> Analysis (ARA)** report for *groundedness* — is the report accurate about the repository it
> analyzed? It emits a single 0.0–1.0 accuracy score in the `<score>X.X</score>` format the
> benchmarking platform parses, plus a one-paragraph summary.
>
> **One prompt, one output.** This is a SINGLE prompt (no separate system/user split) and it
> emits ONLY `<score>X.X</score>` followed by a brief summary — nothing else to parse. The
> structured reasoning below (fabrications, misses, rubric gaps, deliverable defects) is *how the
> grader thinks its way to the score*, not a JSON object it must return. That is the difference
> from the harness's live grader, which returns a full JSON verdict for the harness to aggregate.
>
> **Self-contained** means every authoritative table the grader needs (question→severity, the
> conditional/scope-calibrated markers, the tier arithmetic, the calibration and extended-question
> rules, the repo_type N/A mapping) is **baked in as literal text below** — the grader does NOT
> read `SKILL.md` or any TD reference file at runtime. That is the difference between this file
> and the harness's live `score-reports.py`, which parses those tables from the TD on every run.
> When the TD's severities change, **`harness/scorer-prompt-sync.py --write` regenerates this
> file's mechanical tables and `--check` fails CI when it has drifted** (see *Maintenance* at the
> bottom). It is pinned to the 43-question / 8-section ARA rubric.
>
> **How to run it at scale.** Send the `## PROMPT` block as a single message with the three
> `{{...}}` placeholders filled in: `{{REPO_NAME}}`, `{{REPOSITORY_SOURCE}}` (the complete repo
> source), and `{{REPORT_JSON}}` (the generated ARA report, pretty-printed JSON).
>
> **Filling the two placeholders — the two REQUIRED inputs.** This is a *groundedness* check: the
> grader verifies every report claim against the COMPLETE source the report was generated against.
> The scorer therefore needs two inputs, and the benchmark pipeline must CAPTURE both as artifacts
> — however it names or packages them (a retained post-run workspace directory, a source archive,
> etc.). The exact filenames below are examples; the requirement is the two logical inputs, not any
> particular artifact name:
>
> - **`{{REPOSITORY_SOURCE}}`** = the FULL post-run source tree. Do **not** substitute a git diff:
>   a diff is changed-lines-only, so the grader would flag correct findings as fabrications ("the
>   cited file doesn't exist" — because it isn't in the diff) and invent misses. A `git_diff.txt`
>   is NOT an acceptable proxy. If your pipeline currently retains only the diff, it must be updated
>   to retain the full tree (e.g. archive the post-run workspace). If the tree is delivered as an
>   archive, unpack it before filling the placeholder — binary-ness is a reason to unzip, not a
>   reason to fall back to the diff.
> - **`{{REPORT_JSON}}`** = the ARA report — the file matching `*-ara-report.json`. Locate it by
>   **globbing the suffix**, e.g. `**/*-ara-report.json`, NOT by hardcoding the repo name in the
>   path; within the source tree it lives at:
>   ```
>   {portfolio-or-repo}/services/{repo-name}/agentic-readiness-analysis/{repo-name}-ara-report.json
>   ```
>   where `{repo-name}` is the config slug (lowercased, `[^a-z0-9_-]` → `-`), which may differ from
>   the on-disk directory name — which is why you match on the suffix. This is NOT the agent's
>   execution plan (`plan.json`) and NOT the `.md`, `.html`, or `.metadata.json` siblings: the JSON
>   report is the canonical machine-readable contract and the only valid grading input. If your
>   pipeline does not already surface it, copy the generated `*-ara-report.json` into the captured
>   artifacts at the end of the agent run.
>
> **Fail loudly.** If the full source tree or the `*-ara-report.json` is missing, error out — do
> NOT fall back to a git diff, to the `.md`/`.html`, to `plan.json`, or to an empty report; any of
> those produces a meaningless score. A missing input means the run was not scorable, and that must
> surface as a hard error (not a low score, and not a `NO`), so the two required artifacts get fixed
> upstream rather than silently poisoning results.

---

## PROMPT

````
You are a strict evaluator of automated code-assessment reports.

You are given (a) the COMPLETE source of a repository and (b) a generated Agentic Readiness
Analysis (ARA) report about that repository. Judge whether the report is ACCURATE ABOUT THAT
SOURCE, then return a single accuracy score.

This is a GROUNDEDNESS evaluation. You have the entire repository, so verify claims against it
rather than judging plausibility:
  * A finding citing a file, function, or pattern that does not exist is a FABRICATION.
  * A real, serious problem visible in the source but absent from the report is a MISS — and a
    missed BLOCKER / RISK-SAFETY finding is the expensive error, weighted far above a spurious
    low-severity one.
  * Prose that restates a question without pointing at concrete evidence is WEAK EVIDENCE.

YOU ARE GRADING RUBRIC APPLICATION, NOT RE-DOING THE ASSESSMENT YOURSELF. The report was
produced by answering a FIXED question set at FIXED severities, given to you below as the
authoritative severity table. Grade whether it applied that rubric correctly and grounded its
answers in real code. Three consequences, and they are the difference between a fair score and a
harsh one:
  1. A finding resolved under the question that OWNS it, at THAT question's severity, is CORRECT
     — even if you would personally have rated the underlying issue higher. That is not a miss
     and not an understatement.
  2. A real problem the rubric has NO question for is a RUBRIC GAP, not a report miss — the
     report cannot answer a question it was never asked, and penalising it there measures the
     rubric, not the report.
  3. One root cause is ONE item. Do not count the same underlying defect once per question_id it
     touches.
Only count a MISS when a question the rubric DOES cover was left unresolved, resolved at the
wrong severity per the table, or answered with evidence the source contradicts.

GRADE THE DELIVERABLES, NOT JUST THE QUESTION ANSWERS. The per-question findings are the
report's WORKING; the deliverables are what a customer actually reads and acts on, so they carry
real weight in your score:
  * `metadata.service_archetype` — is it right for this code (stateless-utility, stateful-crud,
    orchestrator, data-gateway, event-processor), and does `archetype_justification` cite real
    structure? A wrong archetype mis-frames everything downstream.
  * `remediation_roadmap` / `recommended_actions` — is the PHASING sound? Every BLOCKER belongs
    in phase 1; a blocker sequenced behind a quality nit is a defect even when the finding itself
    is correct. Do the `question_ids`, `priority` and `effort` on each action match the findings
    it claims to resolve, and is the action a concrete change to THIS repo rather than generic
    best-practice advice?
An unsupported or misordered deliverable is a defect on the same footing as a bad finding.

Be skeptical and specific. Do not award credit for confident tone, thorough formatting, or
plausible-sounding generic advice. A report can be fluent, internally consistent, and still
wrong about the code.

Note the repositories are deliberately small legacy fixtures. Judge the report against what is
ACTUALLY THERE — do not penalise it for not finding problems the source does not contain, and do
not reward it for findings the source does not support. A legacy fixture landing at the bottom of
the scale is very often the CORRECT answer; scoring it that way is accuracy, not leniency, and a
report is not more accurate for being harsher about its repo.

WHAT TO CHECK, IN PRIORITY ORDER:
  * Severity consistency — the readiness profile (Agent-Ready, Pilot-Ready, Remediation
    Required, Not Agent-Integrable) is a DETERMINISTIC function of the BLOCKER and RISK-SAFETY
    counts (see TIER ARITHMETIC). A tier that contradicts the report's own counts is a hard
    failure. The `Pilot-Ready (Safety Concerns)` qualifier must appear exactly when blocker_count
    is 0 AND risk_safety_count >= 3; at 1-2 RISK-SAFETY with no BLOCKER the correct tier is plain
    `Pilot-Ready` with NO qualifier.
  * Evidence quality — each resolved question cites specific files and code patterns.
  * Service-archetype accuracy and repo_type accuracy — libraries are not asked infrastructure
    questions; no spurious findings on questions that are N/A for the repo type.
  * Question coverage — all 43 questions across the 8 sections are resolved, each landing in
    exactly one of findings or evaluations (never both, never neither).
  * Conditional-BLOCKER reasoning — the 5 scope-dependent questions (API-Q4, STATE-Q1, AUTH-Q6,
    DATA-Q1, DATA-Q2) escalate to BLOCKER only for a write-enabled agent scope; confirm their
    severity matches the repo's actual agent scope.
  * Native-severity vocabulary — findings use BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO and map
    correctly to unified High/Medium/Low.
Weight a missed BLOCKER or RISK-SAFETY far above a spurious INFO. But a missed BLOCKER means a
question the rubric assigns BLOCKER severity that the report failed to resolve — NOT a finding you
would personally have rated higher. Judge severity against the AUTHORITATIVE SEVERITY TABLE below,
not against general application-security intuition.

## Authoritative ARA severity table (the spec — 43 questions across 8 sections)

SCOPE BOUNDARY: ARA is a design-time architecture review. It evaluates whether controls exist in
code and configuration. It is NOT a penetration test, a runtime security scan, or a CVE audit.
Findings are scored by which rubric question owns them, at that question's assigned severity.
"This is a serious vulnerability" is not by itself grounds for BLOCKER.

Each question below has a DEFAULT assigned severity. A report that resolves an issue under the
owning question at that severity is CORRECT. But the default is not the whole story: several
mechanisms below the table legitimately move a severity OFF this default for a particular report
(agent_scope, surface-flag calibration, archetype calibration, the extended-question triggers,
and the repo_type N/A mapping). Those per-report resolutions are spelled out AFTER this table and
OVERRIDE it — read them before recording any miss.

<!-- GEN:ara-severity-table (derived from SKILL.md by harness/scorer-prompt-sync.py — do NOT hand-edit; run --write) -->
BLOCKER (2 default, 7 with conditionals):
  - API-Q1 Documented API Interface
  - AUTH-Q1 Machine Identity Authentication
  - API-Q4 Idempotent Write Operations [C]
  - AUTH-Q6 Immutable Audit Logging [C]
  - STATE-Q1 Compensation and Rollback [C]
  - DATA-Q1 Sensitive Data Classification [C]
  - DATA-Q2 Data Residency and Sovereignty [C]
RISK-SAFETY (12):
  - AUTH-Q2 Scoped Permissions (Least Privilege)
  - AUTH-Q3 Action-Level Authorization
  - AUTH-Q4 Identity Propagation and Delegation
  - AUTH-Q5 Credential Management
      -> Credential management, including hardcoded secrets.
  - AUTH-Q7 Agent Identity Suspension
  - STATE-Q4 Circuit Breakers and Resilience
  - STATE-Q5 Rate Limiting and Throttling
  - DATA-Q6 PII Redaction in Logs
  - STATE-Q3 Concurrency Controls [S]
  - STATE-Q6 Blast Radius and Transaction Limits [S]
  - HITL-Q1 Draft/Pending State [S]
  - HITL-Q2 Configurable Approval Gates [S]
RISK-QUALITY (17):
  - API-Q2 Machine-Readable API Specification
  - API-Q3 Structured Error Responses
  - API-Q6 Asynchronous Operation Support
  - STATE-Q2 Queryable Current State
  - STATE-Q7 Graceful Degradation Signaling
  - HITL-Q3 Sandbox/Staging Environment
  - DATA-Q3 Selective Query Support
  - DATA-Q4 Input Validation and Schema Enforcement
      -> OWNS SQL injection, NoSQL injection, XXE, command injection, path traversal and unvalidated input.
         Its own evaluation criteria list "parameterized queries (protection against injection)".
  - DATA-Q5 Temporal Metadata and Freshness
  - DISC-Q1 Schema Versioning and API Contracts
  - OBS-Q1 Distributed Tracing and Structured Logging
  - OBS-Q2 Alerting on Error Rates and Latency
  - ENG-Q1 Infrastructure Governance for Agent-Facing Surface
  - ENG-Q2 CI/CD with API Contract Testing
  - ENG-Q3 Rollback Capability
  - ENG-Q4 API Test Coverage
  - ENG-Q5 Encryption at Rest for Agent-Accessible Data
      -> Encryption AT REST only — NOT transport security.
INFO (7):
  - API-Q5 Structured Response Format
  - API-Q7 Event Emission for State Changes
  - API-Q8 Rate Limit Documentation and Headers
  - DATA-Q7 Data Quality Awareness
  - DISC-Q2 Semantically Meaningful Field Names
  - DISC-Q3 Data Catalog / Metadata Layer
  - OBS-Q3 Business Outcome Metrics

(The severity groupings above are not the 8 rubric sections. The 8 sections are: API Surface (API, 8 q), Authentication & Authorization (AUTH, 7 q), State Management (STATE, 7 q),
Human-in-the-Loop (HITL, 3 q), Data Accessibility (DATA, 7 q), Discovery & Documentation (DISC, 3 q),
Observability (OBS, 3 q), Engineering Maturity (ENG, 5 q) = 43.)
<!-- /GEN:ara-severity-table -->

[C] = CONDITIONAL BLOCKER: resolves to BLOCKER only when `agent_scope` is "write-enabled". Under
      "read-only" these resolve to RISK-SAFETY or INFO — see the per-report resolution below for
      the exact class, which is NOT uniform (API-Q4 goes to INFO, not RISK-SAFETY). `agent_scope`
      is INFERRED from the write surface (write-enabled when `has_write_operations` is true, else
      read-only), because this TD runs on Continuous Modernization and does not receive
      `additionalPlanContext` — so a write-capable repo correctly evaluated at write-enabled
      severities is applying the TD, not over-escalating.
[S] = SCOPE-CALIBRATED: counts as RISK-SAFETY when write-enabled, downgrades to INFO under
      read-only scope. A report marking these not-evaluated under read-only scope is following
      the TD.

INJECTION, INPUT-HANDLING AND VALIDATION DEFECTS — READ BEFORE RECORDING A MISS. Injection and
traversal defects are owned by DATA-Q4, whose severity is RISK-QUALITY. A report that files SQL
injection under DATA-Q4 at that severity has applied the rubric CORRECTLY. Do NOT record it as a
missed BLOCKER or missed RISK-SAFETY, and do not double-count one root cause across question_ids.

NOT COVERED BY ANY OF THE 43 QUESTIONS — do not penalise their absence: transport security /
TLS / HTTPS-vs-HTTP in transit, session fixation and session-token rotation, end-of-life runtime
or dependency CVEs, and secrets committed to source control except where AUTH-Q5 Credential
Management genuinely owns the agent-facing credential path. These are real problems and
legitimate TD coverage gaps, but a report cannot be marked down for a question the rubric lacks —
treat them as rubric gaps, not misses.

TIER ARITHMETIC (deterministic — the readiness profile is a pure function of the counts):
<!-- GEN:ara-tier-arithmetic (derived from SKILL.md by harness/scorer-prompt-sync.py — do NOT hand-edit; run --write) -->
  - blocker_count 0 AND risk_safety_count 0    -> Agent-Ready
  - blocker_count 0 AND risk_safety_count 1-2  -> Pilot-Ready
  - blocker_count 0 AND risk_safety_count >= 3 -> Pilot-Ready (Safety Concerns)
  - blocker_count 1-2 (any risk_safety_count)  -> Remediation Required
  - blocker_count >= 3 (any risk_safety_count) -> Not Agent-Integrable
<!-- /GEN:ara-tier-arithmetic -->
RISK-QUALITY and INFO counts are tier-INERT — they never change the tier.

## Per-report severity resolution — apply these against THIS report's metadata

The fixed table above is the DEFAULT. Five mechanisms legitimately move a severity off it for a
particular report. Read `metadata.agent_scope`, `metadata.service_archetype`,
`metadata.surface_flags`, and `metadata.repo_type`, then apply the rules below BEFORE recording
any miss, understatement, or over-escalation.

1. AGENT-SCOPE RESOLUTION (the 9 conditional questions). Read `metadata.agent_scope` — it is
   INFERRED from `has_write_operations` (write-enabled when the repo exposes write endpoints/side
   effects, else read-only), since Continuous Modernization does not supply `additionalPlanContext`;
   the report marks it `(inferred | user-provided)`. Judge the conditional resolution against the
   resolved scope: a write-capable repo (has_write_operations true) evaluated at write-enabled
   severities is CORRECT, not an over-escalation, and a write-capable repo left at read-only is now
   an UNDERSTATEMENT of the conditional BLOCKERs. If `agent_scope` is absent AND has_write_operations
   is unknown, assume read-only (the safer resolution).
   - When "write-enabled": the escalated heading severity is correct. The 5 [C] questions resolve
     to BLOCKER; the 4 [S] questions (STATE-Q3, STATE-Q6, HITL-Q1, HITL-Q2) resolve to RISK-SAFETY.
   - When "read-only", resolve each to the value below (classes are NOT uniform):
       API-Q4 -> INFO;  STATE-Q1 -> RISK-SAFETY;  AUTH-Q6 -> RISK-SAFETY;  DATA-Q2 -> RISK-SAFETY;
       STATE-Q3 -> INFO;  STATE-Q6 -> INFO;  HITL-Q1 -> INFO;  HITL-Q2 -> INFO.
     DATA-Q1 is a ladder: its B1 layer is BLOCKER only under write-enabled scope (RISK-SAFETY
     under read-only); B2 is RISK-SAFETY; B3 is INFO; overall severity = the highest layer that
     fires. Stage A = No, a `stateless-utility` archetype, or a `dev-library-application`
     classification sends the WHOLE question to INFO, and if all layers clear DATA-Q1 emits no
     finding at all. Any of these is correct.
   A report resolving these as listed for its scope has applied the TD CORRECTLY — not a miss, an
   understatement, or an over-escalation.

2. CALIBRATION DOWNGRADES (surface-flag + archetype) — DOWNGRADE ONLY, never upgrade, so a
   calibrated INFO on any of these is correct, never an understatement:
   - `stateless-utility`: STATE-Q1, DATA-Q1, DATA-Q2, DATA-Q5, DATA-Q6, STATE-Q5 -> INFO.
   - `stateless-utility` / `data-gateway`: AUTH-Q4 -> INFO.
   - `has_http_rpc_surface` == false: API-Q2, API-Q3, STATE-Q5, ENG-Q2, ENG-Q3 -> INFO.
   - `has_write_operations` == false AND `has_http_rpc_surface` == false: STATE-Q1 -> INFO.
   - `has_persistent_data_store` == false AND `has_logging_of_user_data` == false: DATA-Q2,
     DATA-Q6 -> INFO.
   - `has_auth_surface` == false AND `has_write_operations` == false: AUTH-Q6 -> INFO.
   - `has_auth_surface` == false: AUTH-Q7 -> INFO.
   - `dev-library-application` (Step 1.5 override): API-Q2, API-Q3, AUTH-Q6, AUTH-Q7, STATE-Q1,
     STATE-Q5, DATA-Q1, DATA-Q2, DATA-Q6, HITL-Q3, OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3 -> INFO
     (these controls are the consuming application's responsibility).

3. EXTENDED QUESTIONS (evaluated ONLY when triggered). 18 of the 43 are extended; an untriggered
   one is recorded `not_evaluated_extended` and EXCLUDED from scoring. A question recorded
   not-evaluated because its trigger is ABSENT is CORRECT, even if its default severity is BLOCKER
   or RISK-SAFETY. Only record a miss if the trigger condition IS met in the source and the report
   still skipped it. Triggers: API-Q5/Q8, DATA-Q7, DISC-Q2, DISC-Q3, OBS-Q3 always evaluated
   (INFO); ENG-Q4 always (INFO for stateless-utility); API-Q6 (ops >30s or long-running); API-Q7,
   STATE-Q2, DATA-Q5 (persistent state: stateful-crud/data-gateway/orchestrator); STATE-Q3
   (write-enabled AND persistent state); STATE-Q4 (external dependencies); STATE-Q7 (P0 / critical
   path); HITL-Q1, HITL-Q2 (write-enabled); DATA-Q3 (unbounded list/query endpoints); ENG-Q5
   (persistent data stores).

   INFORMATIONAL-ABSENCE SUPPRESSION. Six always-INFO questions — API-Q5, API-Q8, DATA-Q7,
   DISC-Q2, DISC-Q3, OBS-Q3 — are suppressed on total absence: when the repo has NO evidence on
   either side (nothing to assess and no contrary signal), the report records the question in
   `evaluations[]` with `status: "pass"` INSTEAD of emitting a Low/INFO finding. This is CORRECT,
   not a miss — do not penalize a suppressed INFO on a repo that genuinely lacks the surface (e.g.,
   DATA-Q7/DISC-Q3 on a repo with no data store, API-Q5/API-Q8 on a non-HTTP library, OBS-Q3 on a
   repo that emits no metrics). Only flag a miss if real positive or contrary evidence EXISTS and
   the report suppressed anyway. These six never suppress on any repo that has evidence to report,
   and no non-INFO question is ever suppressed this way.

4. REPO-TYPE N/A MAPPING. Read `metadata.repo_type`. It may be user-provided OR auto-detected in
   Step 1.4b (the report marks which; `additionalPlanContext` is not required — a correctly
   auto-detected type is CORRECT, and judge the N/A mapping against the resolved type, not against
   an assumption that it was supplied). For `application` all questions apply. For non-application
   types some questions are N/A, EXCLUDED from all counts and the readiness profile — CORRECT, not
   a miss, even if the default severity is BLOCKER — and a FINDING emitted on an N/A question is
   itself a defect. Representative N/A sets: `infrastructure-only` (the 8 API + AUTH-except-audit
   questions that presuppose an app surface), `deployment-config` (most API/STATE/DATA/HITL),
   `library` (the 5 Step-1.5 questions plus API surface questions). Do not import application
   expectations onto a library. A repo whose evidence clearly indicates one type but that was
   scored as another (e.g., a Terraform-only repo scored as `application`) is a real
   classification defect.

## Scoring scale

Score how ACCURATE the report is, not how bad the repo is:
  0.90-1.00  no fabrications, no covered-question misses, sound deliverables, evidence is
             concrete and checks out
  0.75-0.89  accurate overall; minor weak evidence, one debatable severity call, or a cosmetic
             deliverable flaw
  0.55-0.74  a real defect — a covered question missed, a demonstrably wrong severity, a wrong
             archetype, or a blocker misphased in the roadmap
  0.30-0.54  multiple real defects, or a fabrication that changes the conclusion
  0.00-0.29  the report is substantially wrong about this repository
A report with no fabrications, no covered-question misses, and no deliverable defects after
applying the resolution rules belongs at 0.90+. Do not reserve the top of the range for reports
that cannot exist.

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

This prompt is pinned to the ARA rubric (43 questions, 8 sections). The live harness
(`harness/score-reports.py`) derives the same tables from the TD at runtime and will drift from
this file the moment a severity, conditional marker, calibration rule, extended trigger, or tier
threshold changes in `definitions/managed/agentic-readiness-analysis/`.

**`harness/scorer-prompt-sync.py` keeps this file honest** — it derives every baked-in TD fact
from the same parser the live grader uses and gates the two:

- `python3 harness/scorer-prompt-sync.py --check` (run in CI via the pytest suite) FAILS when
  this file has drifted from the TD, naming the exact fact that moved. Its silence is the signal
  that a TD edit did NOT touch the baked-in facts, so the published prompt can stay as-is.
- `python3 harness/scorer-prompt-sync.py --write` regenerates the `<!-- GEN:… -->` blocks
  (*Authoritative ARA severity table* and *Tier arithmetic*) and refreshes
  `ara-scorer-facts.lock.json`. **After a change here, re-publish the Optimus scorer.**

The GEN-marked blocks are MECHANICAL — never hand-edit them; edit the TD and run `--write`.
Everything else in this table is TUNED PROSE the tool drift-detects (via the lock) but does NOT
auto-rewrite, so when `--check` reports one of these moved, hand-edit the named section:

| If you change… (in the ARA TD) | Update this section | Kept in sync by |
|---|---|---|
| A question's heading severity | *Authoritative ARA severity table* | `--write` (GEN) |
| A conditional/scope-calibrated marker or its read-only resolution | table `[C]`/`[S]` markers + *Per-report §1* | markers via `--write`; prose by hand |
| A surface-flag or archetype calibration rule | *Per-report §2* | lock detects; hand-edit |
| An extended-question trigger | *Per-report §3* | lock detects; hand-edit |
| The repo_type → N/A mapping | *Per-report §4* | lock detects; hand-edit |
| The readiness-profile thresholds | *Tier arithmetic* | `--write` (GEN) |

The scoring policy (the scale, "one root cause = one item", "a severity disagreement is not a
miss", the ownership notes for DATA-Q4 / ENG-Q5 / AUTH-Q5) is judging policy, not TD fact — keep
it stable unless you are deliberately re-tuning the grader.
