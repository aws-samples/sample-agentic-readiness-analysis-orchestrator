# Feedback Archive

Items already **shipped**, **rejected**, **already resolved**, **reply-only**, or **docx-only** from the MOD + ARA TD feedback passes. Kept here for CR and reviewer traceability — the live TODO is in `kiro-feedback-todo.md`.

**Last updated:** Apr 29, 2026 — verified shipped items via grep against live TDs.

---

# ✅ MOD TD — Shipped

All items below are **confirmed present in `modernization-assessment/transformation_definition.md`** as of Apr 29, 2026.

## Phase A — Scope + structural

- ✅ **A1 — P1C-1: AWS scope statement.** Prepended AWS-targeting paragraph above `This assessment does NOT cover:` in Summary. Addresses C5 (Turrini), Thread 4.
- ✅ **A2 — P4-1: Name the 5 dimensions** on the `37 questions across 5 sections:` line. Addresses C3 (Omran).

## Phase B — Scoring rubric precision

- ✅ **B1 — INF-Q1 Score 4**: service-count-based criterion. Measured by `≤1 EC2-based service remains`.
- ✅ **B2 — INF-Q2 Scores 2 and 3** (WF-1 wording). Score 2: *"Main production databases are managed services but deployed single-AZ or without Multi-AZ failover enabled. OR: mix of managed and self-managed..."*
- ✅ **B3 (partial) — INF-Q4 archetype-visibility Note.** INF-Q4 has a `> **Note:**` block above Archetype Calibration. **Still open for INF-Q3, APP-Q3, APP-Q4** — in live TODO.
- ✅ **B4 — INF-Q7 Scores 3 and 2**: custom vs default scaling policies (Score 2 explicitly calls out "default/out-of-box settings").
- ✅ **B5 — APP-Q2 Scores 3 and 2**: schema separation + circular dependencies.
- ✅ **B6 — APP-Q5 Scores 3 and 2**: "most endpoints follow" vs "fewer than half".
- ✅ **B7 — SEC-Q3 Scores 3 and 2**: auth method vs coverage (Score 3 allows internal/private-subnet endpoints without auth if network isolation; Score 2 = API key/static credential OR token-auth on <half).
- ✅ **B8 — SEC-Q5 Scores 3 and 2**: what's in env vars (Score 3 = primary credentials in Secrets Manager, non-critical configs may be env vars; Score 2 = production DB creds still in env vars).
- ✅ **B9 — SEC-Q7 Scores 2 and 1**: eliminated overlap (Score 2 = dependency scanning only OR on-demand SAST; Score 1 = nothing).
- ✅ **B10 — SEC-Q3 Score 4** (WF-3): carve-out for intentional public APIs (*"intentionally public endpoints protected by API Gateway with throttling and validation"*).
- ✅ **B11 — analysis-C12: APP-Q1 tone fix.** Score 1 now reads: *"Languages with limited AWS SDK and cloud-native tooling (e.g., COBOL, VB6, Classic ASP) — requires custom integration or migration planning for cloud services."*
- ✅ **B12 — SEC-Q2 Score 2/3 overlap** (analysis-C23): reworked on key type AND coverage.
- ✅ **B13 — INF-Q9 multi-AZ wording** (analysis-C15): Score 3 reads *"stateless compute may be single-AZ if replaceable via ASG/service across AZs."*
- ✅ **B14 — INF-Q10 look-for scope** (analysis-C10): expanded to include CloudWatch alarms, Route 53 health checks, Backup plans.

## Phase C — Terminology

- ✅ **C1 — "compute tiers" → "compute resource types"** (INF-Q7 Score 4). 0 hits for `compute tiers` in TD.
- ✅ **C2 — "primary database" → "main production database"** in INF-Q8 Score 2 and INF-Q9 Score 3.

## Phase D — Missing AWS services

- ✅ **D1 — App Mesh references removed from MOD TD.** 0 hits.
  > ⚠️ **ARA TD status pending** — P0.4 in live TODO. If App Mesh still present in ARA, extend D1 scope.
- ✅ **D2 — AppSync + IoT Core added to INF-Q6** (question + look-for).
- ✅ **D3 — `appspec.yml` (CodeDeploy) added to CI/CD discovery.**
- ✅ **D4 — MWAA added to INF-Q3** workflow orchestration list.
- ✅ **D5 — Amazon MQ added to INF-Q4** (question + look-for).
- ✅ **D6 — Neptune + Timestream added to INF-Q2** (question + look-for).

## Phase E — Content enhancements

- ✅ **E1 — P4-2: DATA-Q1 S3 access-pattern assessment.** Why-it-matters now reads: *"Assessing current access patterns (frequency, size, format) helps identify S3 adoption opportunities and migration paths."*
- ✅ **E2 — P4-4: S3 File Gateway in DATA-Q1 Score 2 note.** *"Amazon S3 File Gateway (mountable S3 access) can bridge filesystem-dependent applications without data duplication."*
- ✅ **E3 — P4-5: DMS/SCT moved out of INF-Q2 why-it-matters.** DMS/SCT now only referenced in Pathway sections (Move to Managed Databases / Move to Open Source), which is correct.
- ✅ **E4 — P4-6: INF-Q11 question clarifies app + IaC pipelines.** Question reads *"Are CI/CD pipelines automated with build, test, and deploy stages for both application code and infrastructure as code, or are deployments manual?"*
- ✅ **E5 — WF-2: Broaden "containerize as-is" to include serverless.** APP-Q2 why-it-matters: *"containerize, migrate to serverless (Lambda), strangler fig extraction, or full decomposition."*

## Phase F — Net-new additions

- ✅ **F1 — Thread 53: SCPs replaced in OPS-Q9 Score 4.** Rewrite uses IaC enforcement + Tag Policies + AWS Config rules. Look-for note: *"SCPs are generally not recommended for tag enforcement — per-service action variance and policy-size limits make them unreliable for tagging; reserve SCPs for security guardrails."*
- ✅ **F2 — Thread 29: Cross-region in INF-Q8 Score 4.** *"cross-region backup replication configured for critical data."*
- ✅ **F3 — Thread 41: DATA-Q3 Score 4 versioning update process.** Score 4 now reads: *"All database engine versions explicitly pinned in IaC; no engines at or past EOL; documented version-update procedure exists covering downtime windows, rollback, and risk acknowledgment."*
- ✅ **F4 — Thread 44: SEC-Q2 Score 4 centralized key management + documented rotation policy.**

## Phase R-reworks — partial rejections with counters applied

- ✅ **R3-rework — INF-Q7 broadening.** Question + why-it-matters + look-for + rubric all shipped:
  - Question: *"Are auto-scaling mechanisms configured for compute, database, and other workloads?"*
  - Why-it-matters names *"DynamoDB capacity, Aurora replicas, ElastiCache shards"*.
  - Score 3: *"covering both compute and data layers"*.
  - Score 2: *"coverage is limited to compute with no scaling on data or other managed services"*.
  - Look-for names `aws_appautoscaling_*`, Lambda concurrency, DynamoDB auto-scaling, Aurora auto-scaling, ElastiCache shard scaling.
  - **Still open:** F6 (business-metric-driven scaling at Score 4) — in live TODO.

## Phase G — Landed

- ✅ **G3 — SEC-Q5 Score 1 + Score 4 rework** (N8). INF-Q5 Score 4 references PrivateLink, VPC Lattice, IPAM, zero-trust patterns. Score 1 references default VPC and public-facing EC2 without isolation.

---

# ✅ ARA TD — Shipped

All items below are **confirmed present in `agentic-readiness-assessment/transformation_definition.md`** as of Apr 29, 2026.

## Part A

- ✅ **ARA-A1 — C34 (Riggs): AgentCore Identity in AUTH-Q1 look-for.** *"Bedrock AgentCore Identity configurations"* added to look-for list.
- ✅ **ARA-A2 — C31 (Riggs): AUTH-Q4 subject/actor phrasing.** Why-it-matters: *"The user is the subject (whose data and permissions apply); the agent is the actor (executing the operation). The system must distinguish both dimensions."*
- ✅ **ARA-A3 — C24 (Riggs + RP): Dual-purpose framing in Objective.** *"(1) portfolio-level telemetry... (2) use-case-level dependency checking — given a specific agent workflow, which target systems are blockers?"*
- ✅ **ARA-A4 — C26 (Harish): Remediation guidance in Summary.** Report now includes *"Prioritized remediation guidance per BLOCKER and RISK finding."*
- ✅ **ARA-A5 — C25 (Henry): Design-time clarification.** *"ARA is a design-time architecture review — it evaluates whether controls exist in code and configuration, not whether they are effective at runtime. It is not a penetration test or runtime security scan."*
- ✅ **ARA-A6 — C22 + C29: Extended "does NOT cover" list.** Line 172: *"...agent-level AI governance (model policy, prompt-injection defense, safety evaluation)..."*
- ✅ **ARA-A7 — C17 (Harish): HITL framing in Step 5 intro.** *"ARA measures whether a target system can support human-in-the-loop patterns, not whether HITL is mandatory. HITL is a valuable safety mechanism..."*
- ✅ **ARA-A8 — AUTH-Q4 duplicated Look-for cleanup.** AUTH-Q4 Look-for is a clean single list at lines ~720-730. No duplication.
- ✅ **ARA — App Mesh in ARA TD.** 0 hits. D1 extension complete, no action needed.

## Part B

- ✅ **ARA-B1 — C30 (Riggs): Control-layer note in Summary.** *"Controls evaluated here may exist at the application layer, the platform layer (API Gateway, service mesh, IAM), or the agent architecture layer..."*
- ✅ **ARA-B2 — C12 counter: MCP-awareness clause in Step 2.** Line 529: *"When MCP-native integration is the target, the findings here inform what an MCP server wrapping this system will need to expose."*
- ✅ **ARA-B3 — C33 partial: AUTH-Q2 scoped permissions phrasing.** AUTH-Q2 why-it-matters: *"Without scoped permissions, the system cannot scope down agent access per capability..."*
- ✅ **ARA-B4 — C11 counter: AUTH-Q4 multitenancy cross-reference.** *"When the target system serves multiple tenants, weak identity propagation compounds with data-layer risks — see DATA-Q2 (data residency) and DATA-Q6 (PII in logs). Treat these as a cluster when planning remediation."*

---

# ❌ MOD TD — Rejected (with counter-proposals)

Each rejection has a counter-proposal that was or will be applied elsewhere. Surface these in CR descriptions so reviewers see their concern was addressed, not dismissed.

- **R1 — Task 10 (P1-B): Reframe APP-Q1 from "language modernity" to "SDK + agent framework coverage."**
  **Rejected as written.** The replacement collapses language maturity into agent-framework availability — an ARA concern, not MOD. Also loses the legitimate "legacy language → modernization blocker" signal (COBOL/VB6/Classic ASP).
  **Counter:** B11 (shipped ✅) fixes the tone without the reframe. If SDK/agent coverage needs capturing, add a new question (APP-Q7) or move to ARA.

- **R2 — Task 9: "in IaC" → "in Terraform/CloudFormation" (two lines).**
  **Rejected.** TD uses "IaC" as superset in ~6 other places and discovery includes CDK, Helm, Kustomize, Ansible. Narrowing two instances excludes CDK (AWS-native) and creates cross-TD inconsistency.
  **Counter:** Drop the task. Current wording is consistent.

- **R3 — Task P4-3: Broaden INF-Q7 beyond compute auto-scaling.**
  **Needs rework, not straight reject.** Question + why-it-matters + look-for edits are fine, but rubric rows still need expansion to cover compute AND data/managed-service auto-scaling. **Still in TODO as "R3-rework"** — sequence R3 → F6 to avoid stomping edits.

- **R4 — analysis-C24 (Robert + Maia): "Plaintext credentials = security blocker, not low score."**
  **Rejected — scope mismatch with MOD's scoring model.** MOD uses 1–4 numeric scoring. BLOCKER/RISK/INFO severity is an ARA construct. Importing it into MOD would break overall/category score math, pathway triggers, and N/A handling.
  **Counter:** Keep SEC-Q5 = 1 for plaintext credentials in MOD, but strengthen the **recommendation text** in the Report Template to flag "address before any modernization work" — deliver severity signal through recommendation copy, not score type.

- **R5 — analysis-C21 (Robert): "CloudTrail belongs in WAFR, not modernization."**
  **Rejected — intentional overlap.** CloudTrail presence is a prerequisite for any auditable modernization work. Lucas already replied with this reasoning in-thread.
  **Counter:** Close thread with existing reply. Keep SEC-Q1 as-is.

---

# ❌ ARA TD — Rejected (with counter-proposals)

- **ARA-R1 — C12/C14/C15 (Mark + RP): "Evaluate MCP interfaces as first-class target."**
  **Rejected.** The TD explicitly excludes MCP servers (line 165). Agent architecture — which MCP is — is not what ARA evaluates; ARA evaluates what agents *call*. Adding MCP rubrics would require new scoring across API-Q1–Q4 and AUTH-Q4, which is a scope reversal requiring leadership sign-off.
  **Counter:** ARA-B2 (TODO — one-line awareness clause in Step 2).
  **Respond in docx thread:** *"Current API surface is assessed because that's what agents call today. MCP is covered by bridge-mode guidance and agent architecture (out of scope per intro)."*

- **ARA-R2 — C11 (Justin): Escalate AUTH-Q4 severity beyond RISK.**
  **Rejected severity change.** Severity model is deliberate:
  - AUTH-Q1 (Machine Identity) = BLOCKER handles the categorical "no identity = no multitenancy" case.
  - AUTH-Q4 = RISK-SAFETY handles the "identity exists but propagation is weak" case. Maps to Pilot-Ready (1–2 RISK-SAFETY) by design.
  - Escalating AUTH-Q4 would push many repos from Pilot-Ready to Remediation Required on architecture maturity, not actual agent-safety risk.
  **Counter:** ARA-B4 (TODO — multitenancy cross-reference, no severity change).

- **ARA-R3 — C33 MCP reference.**
  **Partial reject.** Scoped permissions phrasing is adopted in ARA-B3 (TODO). MCP reference is dropped (same reasoning as ARA-R1).

---

# 📄 Docx-only items (not TD work)

These target the companion docx (`modernization-readiness-assessment-v2.docx` / `agentic-readiness-assessment-v3.docx`) — intro framing, Customer Positioning, Programs tables, Appendix narratives. **Handled in docx review pass, not the TD edit cycle.**

## MOD docx

| Analysis ID | Topic | Docx location |
|-------------|-------|---------------|
| C22 | "WAR" → "WAFR" abbreviation | Scope Boundary narrative |
| C6 | "Assessment vs questionnaire" framing | Intro / opening narrative |
| N7 / Thread 2 | Cross-validate with Cloud Maturity Assessment 3.0 | Intro or Appendix |

## ARA docx

| Analysis ID | Topic | Docx location |
|-------------|-------|---------------|
| C16 | EBA hyperlink | Appendix 3 Programs table |
| C21 | Self-serve + managed delivery model | Customer Positioning section |
| C19 | "Relationship to OLA" — assessment fatigue | How to Use This Guide (new section) |
| C27 | MOD cross-reference (docx narrative) | Intro / opening narrative |
| C18 | "When to run" timing guidance | How to Use This Guide |
| C23 | "target systems" vs "source systems" glossary | Docx glossary |
| C29 (part) | Delineation from "AI team's readiness assessment" | Intro narrative |

---

# 💬 Reply-only items (neither TD nor docx edits)

Respond in the reviewer thread. No TD or docx edit.

## MOD reply-only

| Analysis ID | Topic | Suggested response |
|-------------|-------|--------------------|
| C5 (Gianfranco) | Additional languages — Rust, Ruby? | Confirm current coverage (APP-Q1 mentions them); roadmap note is future work, not TD-bound. |
| C14 (Ahmed) | Positive feedback | Thank and close. |
| C20 (Robert) | Example of sync vs async distinction | Lucas already replied; archetype calibration (Step 2 INF-Q4) handles this — link to existing calibration table. |
| C21 (Robert) | CloudTrail in WAFR | Covered by R5 rejection rationale. |
| C25 (Robert) | Comment-resolution process | Process ack, no TD change. |
| C28 (Maia) | Business metrics auto-scaling (→ F6) | Confirm tracked as F6 pending R3 rework. |
| C36 (Maia) | Why focus on error budget tracking | Respond with OPS-Q3 positioning; defer rebalancing. |
| C37 (Robert) | Secrets Management scoring context | Confirm SEC-Q5 rubric is intentional — respond in thread. |

## ARA reply-only

| Analysis ID | Topic | Suggested response |
|-------------|-------|--------------------|
| C32 | "Why RISK not BLOCKER?" | *"AUTH-Q2/Q3 are RISK-SAFETY because the control can be enforced at the platform layer (API Gateway, IAM) even if the app is coarse-grained. BLOCKER is reserved for categorical failures like no machine identity at all."* |
| C28 | "Does it assess data exposure, privilege escalation, destructive actions?" | Mapping: data exposure → DATA-Q1/Q2/Q6; privilege escalation → AUTH-Q2/Q4; destructive actions → STATE-Q1/Q5/Q6. All covered. |
| C13 | "guarantees?" | Needs anchor ID in docx before responding. |
| C14 | "but does look at MCP interface definitions?" | Covered by ARA-R1 response. |
| C15 | "why not MCP server interfaces?" | Covered by ARA-R1 response. |
| C10 | "Post-readiness POV — what comes next?" | Point to AI DLC workshop (already referenced in docx) and any agent-side readiness assessment. Out of ARA scope. |
| C9 | "Example of what you mean?" | Blocked — need comment anchor in docx. |

---

# 📚 Already resolved (per analysis doc — no work)

**MOD resolved before review:** C1 (Agent Storming — ARA, not MOD), C14 (positive), C20 (sync vs async), C27 (Maia direct edit), C30 (compute tiers).

**ARA resolved before review:** C1 (Agent Storming), C2 (FinOps), C3 (multi-agent framing), C4 (portfolio metrics), C5 (Gartner citation), C6 (process modeling), C7 (EBA criteria), C8 (AI DLC).

---

# MOD Analysis-doc cross-reference

For reviewer look-up — maps analysis IDs to TODO/archive/rejection tracking.

| Analysis ID | Topic | Tracked as |
|-------------|-------|-----------|
| C2 | Remove App Mesh | D1 ✅ |
| C3 | Scope clarification | A1 ✅ |
| C4 | S3 access patterns | E1 ✅ |
| C7 | AppSync + IoT Core | D2 ✅ |
| C8 | IaC / Terraform consistency | R2 (rejected) |
| C9 | Async-only bias | B3 archetype note — partial (INF-Q4 ✅, INF-Q3/APP-Q3/APP-Q4 TODO) |
| C10 | INF-Q10 look-for scope | B14 ✅ |
| C11 | appspec.yml / CodeDeploy | D3 ✅ |
| C12 | Language scoring tone | R1 (rejected reframe) + B11 ✅ (tone-only fix) |
| C13 | Multi-region backup wording | F2 ✅ |
| C15 | Multi-AZ statelessness | B13 ✅ |
| C16 | MWAA | D4 ✅ |
| C17 | Amazon MQ | D5 ✅ |
| C18 | Neptune, Timestream | D6 ✅ |
| C19 | Define "tiers" | C1 ✅ |
| C22 | WAR → WAFR | docx-only |
| C23 | SEC-Q2 Score overlap | B12 ✅ |
| C24 | Plaintext credentials = blocker | R4 (rejected) |
| C26 | VPC Lattice, PrivateLink, IPAM | G3 ✅ |
| C27 | Maia direct edit Apr 24 | resolved |
| C30 | "compute tiers" | C1 ✅ |
| C31 | Version update process | F3 ✅ |
| C32 | Key management + rotation | F4 ✅ |
| C33 | SCP tagging fix | F1 ✅ |
| C34 | DMS/SCT misplaced | E3 ✅ |
| C37 | CI/CD covers app + IaC | E4 ✅ |

---

# Why we draw these scope lines

**ARA guardrails:**
1. **Target systems, not agents.** Reviewing MCP servers, prompt injection, agent governance, or model policy breaks this guardrail.
2. **Design-time, not runtime.** Reviewing live posture or live credentials breaks this guardrail.
3. **Severity-based, not numeric.** BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO maps to readiness profile. Mixing numeric scoring (as C11/C32 implicitly push toward) breaks the profile math.

**MOD guardrails:**
1. **1–4 numeric scoring is the rubric contract.** Importing BLOCKER/RISK/INFO (C24) would break overall/category score math, pathway triggers, and N/A handling.
2. **Modernization, not operational readiness.** MOD evaluates the work needed to modernize; WAFR/runtime ops are adjacent assessments.
3. **IaC is the superset.** Don't narrow to specific tools (R2).

When a reviewer proposal would cross a guardrail, the pattern is: **reject as written, provide a counter-proposal that stays in scope.** Every rejection in this archive follows that pattern.


---

# 🚢 Commit-to-edit trail

Historical record of which commits shipped which edits during the reviewer pass. Preserved from `kiro-execution-plan.md` after that file was retired (all 61 line items done).

| Commit | TD | Message | Items |
|--------|----|---------|-------|
| `0cda661` | MOD | `chore(mod-td): terminology fixes and missing AWS services (P2B, P3, analysis-C10)` | M1-M11 (C1, C2, D1-D6, B14) |
| `870a67a` | MOD | `docs(mod-td): clarify AWS scope, name dimensions, expand DATA-Q1 and APP-Q2 framing (P1C, P4)` | M12-M19 (A1, A2, E1, E2, E3, E4, E5, B3 partial for INF-Q4) |
| `4b6f32e` | MOD | `refactor(mod-td): sharpen scoring rubric precision (P2A)` | M20-M28 (B1, B2, B4, B5, B6, B7, B8, B9, B10) |
| `762e61d` | MOD | `refactor(mod-td): address reopened reviewer concerns + Herrera Soto pass (APP-Q1 tone, SEC-Q2, INF-Q9, DATA-Q3, INF-Q8, OPS-Q9)` | M29-M35 (B11, B12, B13, F1, F2, F3, F4) |
| `0ea6062` | MOD | `refactor(mod-td): broaden INF-Q7 auto-scaling across compute + data (P4-3)` | M36-M39 (R3-rework) |
| `d93b652` | ARA | `chore(ara-td): housekeeping — App Mesh, AUTH-Q4 cleanup, AgentCore Identity signal` | A1-A3 (ARA-A1, ARA-A8, D1 for ARA) |
| `c2e2e97` | ARA | `docs(ara-td): dual-purpose framing, design-time clarification, governance boundary (C22, C24-C26, C30)` | A4-A8 (ARA-A3, ARA-A4, ARA-A5, ARA-A6, ARA-B1) |
| `befe1ec` | ARA | `docs(ara-td): clarify AUTH and API framing, add multitenancy cross-reference (C11, C12, C17, C31, C33)` | A9-A13 (ARA-A7, ARA-A2, ARA-B4, ARA-B3, ARA-B2) |
| `0836d24` | MOD | INF-Q5 rework — Thread 26 (post-landing) | M40 (G3) |

**Verification commits noted at the time of landing:**
- `compute tiers` → 0 hits ✅
- `App Mesh` → 0 hits in both MOD and ARA TDs ✅
- `primary database` → 0 hits in rubric rows ✅
- AUTH-Q4 Look-for block de-duplicated ✅
- Question count unchanged: MOD = 37 + 1 Report Template anchor; ARA structure preserved ✅


---

# 📊 V3 Impact Summary (from retired v2-vs-v3 comparison)

Preserved from `example-reports/v2-vs-v3-comparison.md` after it was retired. Actionable follow-ups moved into `kiro-feedback-todo.md` as items **C-1** through **C-5**.

## Portfolio-level shifts

| Metric | v2 | v3 | Delta |
|---|---|---|---|
| MOD portfolio score | 2.15 | 2.13 | -0.02 (stable) |
| Score range | 1.40–2.71 | 1.67–2.65 | Lowest pulled up |
| Not Ready count (<1.5) | 1 (unishop) | 0 | -1 |
| Foundational blockers | 22 | 20 | -2 |
| Improvement opportunities | 3 | 5 | +2 |
| Pathways triggered | 6/7 | 5/7 | -1 |
| ARA BLOCKERs | n/a | 9 | new dimension |

Net: v3 is not more lenient — the distribution is sharper. Fewer blockers, more improvement classifications = precision win, not grade inflation.

## Landed and visibly shaping v3 reports

- **Terminology fixes (M1-M4)** — `compute tiers` and `primary database` gone from rubric rows.
- **App Mesh removal (M5 / A1)** — 0 mentions in the 5 target repos' v3 reports.
- **New AWS services (M6-M10)** — MWAA, Amazon MQ, AppSync, appspec.yml all surfacing in v3 findings where relevant.
- **APP-Q1 tone fix + reclassification (M29)** — biggest behavioral shift: unishop 4 → 2, pulling it out of "Not Ready". Exactly what B11 was designed to produce.
- **INF-Q7 broadening (M36-M39)** — v3 findings evaluate both compute and data auto-scaling (DynamoDB throttling, on-demand scaling, etc.).
- **DATA-Q3 version-update procedure (M33)** — v3 explicitly flags missing procedure in 3 of 5 repos.
- **INF-Q8 cross-region backup (M34)** — multi-region concern integrated into backup rubric.
- **INF-Q5 managed networking rework (M40)** — PrivateLink/VPC Lattice/zero-trust evaluation flowing into v3 evidence.
- **AgentCore Identity signal (A3)** — surfacing in eks-saas-gitops AUTH-Q1 finding.
- **OPS-Q9 SCP removal (M35 / F1)** — zero SCP tagging recommendations in v3.

## Landed in TD but not visible in v3 reports (expected, not regressions)

- **ARA Summary/Objective framing (A4-A8)** — TD framing doesn't quote verbatim into reports. See live TODO **C-2**.
- **MCP awareness clause (A13)** — repos in v3 don't expose MCP. See **C-5**.
- **S3 File Gateway note (E2/M18)** — no on-prem migration scenario in v3 to trigger it. See **C-5**.
- **INF-Q11 "application and IaC" phrasing (E4/M16)** — TD edit landed in question header but not in rubric/why-it-matters, so reports still sound app-pipeline-centric. See **C-3**.

## New v3 deliverables

- **Bridge report** — 17 shared remediation mappings, 67% of ARA BLOCKERs resolvable by MOD Phase 0, unified remediation sequence. Worth keeping in mind: the bridge quantifies the ARA/MOD overlap that teams used to plan twice.
- **Portfolio-level question tightening** — PORT-MOD-Q4 / PORT-ARA-Q5 have sharper evidence in v3.

## Things to watch (moved to live TODO)

- **C-1** — APP-Q1 Score 2 may be too harsh for "language modern, stack lag" cases (Java 8 + legacy framework).
- **C-4** — Portfolio Assessment Inventory `assessment_date` pulled from frontmatter, not run date — produces stale dates.

## Phase F+C — Shipped Apr 30, 2026 (branch `fix/ara-calibration`)

- ✅ **B3 — Archetype-visibility Note extended to INF-Q3, APP-Q3, APP-Q4.** Commit `7040e7f`. Added the `> **Note:** This question uses archetype-sensitive calibration...` block above `**Archetype Calibration:**` in all 3 archetype-sensitive MOD questions that were missing it. Now all 4 (INF-Q3, INF-Q4, APP-Q3, APP-Q4) surface archetype sensitivity consistently.
- ✅ **F5 — INF-Q11 ↔ SEC-Q7 cross-reference.** Commit `7040e7f`. Added one sentence to INF-Q11 why-it-matters noting CI/CD automation alone is not sufficient — pipelines must also include security validation (SAST, DAST, dependency scanning). Cross-references SEC-Q7 for the pipeline-security evaluation.
- ✅ **F6 — INF-Q7 Score 4 business-metric-driven scaling.** Commit `7040e7f`. Extended Score 4 to mention *"custom CloudWatch metrics on requests-in-flight, orders-per-second, queue depth"* as the maturity signal where purely technical metrics are insufficient. Completes R3-rework.
- ✅ **C-1 — APP-Q1 two-axis rubric.** Commit `7040e7f`. Rewrote APP-Q1 with a two-axis calibration: (a) language/runtime modernity, (b) framework/SDK modernity. Score 4 = all modern (Python 3.10+, Java 17+ with Spring Boot 3.x and AWS SDK v2, modern .NET 6-10 with AWS SDK v3). Score 3 = modern language with framework/SDK lag (Java 17 + Spring Boot 2.7; modern .NET with SDK v2 partial adoption). Score 2 = compound regression across all three axes (Java 8 + Spring Boot 2.x + SDK v1; .NET Framework 4.x + legacy ASP.NET + SDK v2 or older; also PHP/Ruby/Perl). Score 1 = no meaningful AWS SDK (COBOL, VB6). Scanner data confirmed .NET Framework 4.8 (greenshot) and modern .NET (Sonarr, cartservice) were being conflated at Score 3, and Java 8 alone was scoring 4 in some reports — the new rubric separates these cleanly.

## Phase R — ARA Rubric Recalibration (shipped Apr 29–30, 2026, branch `fix/ara-calibration`)

**Source:** `analyze-ara-patterns.py` across all 34 zg-cmp ARA v4 reports — 26 of 43 questions showed ≥85% concentration on one severity, with 11 non-data-handling OSS tools getting the same BLOCKER/RISK-SAFETY findings as hapi-fhir.

- ✅ **ARA-R1 — DATA-Q1 scope gate + archetype calibration.** Commit `044c369`. Rewritten with Stage A (does this system handle sensitive data?) / Stage B (classification check) structure. `stateless-utility` archetype and `dev-library-application` override land on INFO.
- ✅ **ARA-R2 — DATA-Q2, DATA-Q6 archetype + scope calibration.** Commit `3826b58`. Both downgrade to INFO when the system has no persistent data store and no user-data logging, or for `stateless-utility` archetype. Conditional BLOCKER logic on DATA-Q2 preserved.
- ✅ **ARA-R3 — STATE-Q1, STATE-Q5 archetype calibration.** Commit `3826b58`. STATE-Q1 downgrades to INFO when no write operations and no HTTP/RPC surface. STATE-Q5 downgrades to INFO when no HTTP/RPC surface. Both also honor the dev-library-application override.
- ✅ **ARA-R4 — OBS-Q1, OBS-Q2, ENG-Q1, ENG-Q2, ENG-Q3 library-aware calibration.** Commit `ed9eca6`. All five downgrade to INFO for `dev-library-application` or when no HTTP/RPC surface (and, for ENG-Q1, also no auth surface).
- ✅ **ARA-R5 — API-Q2, API-Q3 scope gate for "no HTTP surface".** Commit `3826b58`. Both downgrade to INFO when `has_http_rpc_surface` is false or for `dev-library-application`.
- ✅ **ARA-R6 — Target-system-surface detection step.** Commit `cf58756`. New Step 1.5 records five surface flags (has_persistent_data_store, has_http_rpc_surface, has_auth_surface, has_write_operations, has_logging_of_user_data). Feeds all downstream scope gates. Renumbered archetype detection to Step 1.6.
- ✅ **ARA-R7 — AUTH-Q6 and AUTH-Q7 differentiation when downgraded.** Commit `dd35bce`. Both downgrade to INFO for `dev-library-application` or when no auth surface (+ no write operations for AUTH-Q6). Conditional BLOCKER logic on AUTH-Q6 preserved.
- ✅ **ARA-R8 — Dev-library-application archetype override (option b).** Commit `cf58756` as part of Step 1.5. When archetype is `stateless-utility` AND 3+ surface flags are `false`, apply the `library` N/A mapping as the scoring baseline. ARA-TD-internal, no Power or portfolio config changes needed.
- ✅ **ARA-R9 — HITL-Q3 library calibration.** Commit `3826b58`. Downgrades to INFO for `dev-library-application` or when no HTTP/RPC surface and no data store.

**Canary verification (Apr 29, 2026):** Ran tqdm, hapifhir, umami with recalibrated TD. tqdm: all 15 targeted questions flipped from BLOCKER/RISK-SAFETY/RISK-QUALITY to INFO. hapifhir: DATA-Q1 correctly stayed BLOCKER (real PHI). umami: unchanged (observability repo that does handle user data). Confirms the calibration removes false positives without under-flagging real data-handling systems.

**Pending:** 31 non-canary repos need v5 ARA re-run against recalibrated TD to confirm V-R1..V-R4 at portfolio scale.

## Phase C-2 — ARA framing lift (shipped Apr 30, 2026)

- ✅ **C-2 — Lift ARA Summary framing into per-question why-it-matters.** Commit `cfe3a04`. The ARA Summary/Objective already carried dual-purpose, design-time, control-layer, and HITL-support-not-mandatory framing, but rendered reports quote per-question why-it-matters (not Summary). Lifted one sentence each into:
  - **AUTH-Q1**: design-time + control-layer clause (machine identity sits at the control layer; weak attribution invalidates downstream AUTH-Q2/Q3/Q6)
  - **AUTH-Q4**: dual-purpose clause (portfolio telemetry vs use-case-level dependency checking)
  - **HITL-Q1**: support-not-mandatory clause (ARA measures whether HITL patterns can be supported, not whether they are mandatory)

## Phase TD-Infra — Fix A + Fix B (shipped Apr 29, 2026)

- ✅ **Fix A — td_version in report metadata.** Commit `c97b735`. Both ARA and MOD reports now emit `td_version` in the frontmatter so we can tell which TD version generated which report during portfolio scans and regressions.
- ✅ **Fix B — Not Evaluated (archetype-N/A) tier for MOD.** Commit `c97b735`. MOD TD now has a `"Not Evaluated (archetype-N/A)"` output tier mirroring ARA's Not-Evaluated handling. Used by archetype-sensitive questions when the archetype makes the question inapplicable (e.g., stateless-utility + APP-Q3 sync-is-correct), so these don't default to Score 4 and skew category averages.

---


## Phase C-5 — Effectively closed by zg-cmp v4 portfolio run (Apr 30, 2026)

- ✅ **C-5 — MCP and File Gateway TD clauses now exercised in example-reports.**
  Original concern was that the A13 MCP awareness clause and the E2/M18 S3 File Gateway note were shipping in the TDs but never firing in any sample portfolio run. Verified Apr 30, 2026 against `example-reports/zg-cmp-full-assessment/modernization-assessment/*.md`:
  - **MCP clause exercised:** Graylog2 MOD report calls out the existing MCP server implementation (`graylog2-server/src/main/java/org/graylog/mcp/` with 13 tools — SearchMessages, ListStreams, AggregateMessages, SystemInfo, ListFields, etc.) as an existing AI/agent foundation. FlowiseAI mentions MCP SDK in the AI stack. sentry-python integration tests cover MCP.
  - **File Gateway clause exercised:** Lidarr, Sonarr, gulpjs, and Graylog2 MOD reports all carry S3 File Gateway recommendations in DATA-Q1 Score 2 context ("Consider Amazon S3 File Gateway for seamless S3 integration without changing filesystem-based code paths"). Multiple repos with filesystem-dependent media/data patterns triggered it.
  No additional sample portfolio needed — the 34-repo zg-cmp run provided natural coverage.


## Phase C-4 — Removed Apr 30, 2026 (orchestrator concern, not TD concern)

- ❌ **C-4 — `assessment_date` in Portfolio Inventory uses frontmatter rather than run date.** *Removed from todo.*
  Original plan was to fix the aggregator in `portfolio-modernization/transformation_definition.md` and `portfolio-agentic-readiness/transformation_definition.md` to source `assessment_date` from file mtime or an injected run timestamp. After reviewing scope: this belongs to the orchestrator (or whatever invokes the TD), not the TD itself. The orchestrator has the run timestamp naturally and can pass it through at invocation time. Closing without TD changes. If the zg-cmp-style date mismatch surfaces again, fix it at the orchestrator/Power layer.


## Phase C-3 / C-6 / C-7 — Shipped Apr 30, 2026 (branch `fix/ara-calibration`)

All three items targeted calibration gaps surfaced by `scan-rubric-quality.py` (2163 MOD findings + 2978 ARA findings across 5 MOD portfolios and 6 ARA portfolios).

- ✅ **C-3 — INF-Q11 rubric rows carry "application + IaC" framing.**
  Rewrote Scores 1-4 to land the application+IaC framing in rendered output (reports quote rubric rows, not just question headers).
  - Score 4: "Full CI/CD automation covering both application code and infrastructure-as-code changes, with test, build, deploy, and automated rollback stages."
  - Score 3: covers both tracks with build+deploy but limited testing, OR automation on one track (application or IaC) with manual steps on the other.
  - Score 2: partial automation with manual/semi-manual deployment for application and/or IaC changes.
  - Score 1: no CI/CD, "all application and infrastructure deployments are manual scripts or ClickOps."

- ✅ **C-6 — MOD SEC-Q5 Score 1/2/3 boundary rewritten for plaintext precision.**
  Scanner showed SEC-Q5 Score 2 absorbing 33 repos with mixed maturity (CloudFormation NoEcho parameters, SSM Parameter Store for admin passwords, repos with remaining plaintext alongside some secret management). Rewrite separates the three cases:
  - Score 1: plaintext credentials present anywhere in the repository — source files, application configs, `.env`, `application.properties`, connection strings in IaC without parameter/secret references. Score 1 applies *even when* a secrets manager exists elsewhere in the system.
  - Score 2: no plaintext in source or version control, but production credentials in plain env vars, parameter store without encryption (`String` not `SecureString`), or CloudFormation `NoEcho` parameters without rotation. Includes mixed-management cases (some secrets in Secrets Manager, at least one still in env vars).
  - Score 3: Secrets Manager/Vault used for all production credentials with rotation on high-risk secrets; non-critical configs may remain in env vars.
  - Score 4: all secrets in Secrets Manager/Vault with automated rotation; no production credentials in env vars.
  Look-for extended with differentiation signals (`SecureString` vs `String`, `rotation_lambda_arn`, CloudFormation `NoEcho` backing).
  Separate from the C24 rejection (which was about BLOCKER severity on SEC-Q5 — not revisited).

- ✅ **C-7 — MOD surface-flag calibration (Step 1.6 + surface gates).**
  Scanner showed INF-Q2 (managed DBs) at 59% Score 1 and SEC-Q2 (encryption at rest) at 86% Score 1 across all portfolios, dominated by OSS libraries and stateless utilities with no persistent-data or at-rest surface at all. MOD-side equivalent of the ARA R1/R6/R8 pattern.
  - Added new **Step 1.6: Target-System Surface Detection** in MOD TD between archetype detection and N/A mapping.
  - Records five surface flags: `has_persistent_data_store`, `has_at_rest_data_surface`, `has_deployed_workload`, `has_api_surface`, `has_multi_instance_deployment`. Derived from the Step 1 file inventory — no additional scanning needed.
  - Surface gates applied:
    - INF-Q2 (Managed Databases) requires `has_persistent_data_store`
    - SEC-Q2 (Encryption at Rest) requires `has_at_rest_data_surface`
    - INF-Q8 (Backup/Recovery) requires `has_persistent_data_store` OR `has_at_rest_data_surface`
    - INF-Q9 (High Availability) requires `has_deployed_workload` AND (`has_api_surface` OR `has_persistent_data_store`)
    - OPS-Q2 (SLOs) requires `has_api_surface` OR `has_persistent_data_store`
  - When a gate flag is `false`, the question records as **"Not Evaluated (archetype-N/A)"** rather than Score 1. Surface flags never downgrade a real Score 1 — they only prevent false Score 1 on systems that don't expose the surface.
  - Inline `> **Note:** This question is **surface-gated** (Step 1.6)...` blocks added to INF-Q2 and SEC-Q2 question sections for assessor visibility (matches the existing B3 archetype-visibility Note pattern).
  - Surface Flags field added to report metadata header alongside Archetype Justification.

**Verification pending:** V-R1 — re-run `scan-rubric-quality.py` against v5 portfolio to confirm SEC-Q2 86% Score-1 concentration drops (libraries and stateless utilities should now land on Not-Evaluated) and INF-Q2 59% concentration drops similarly, without downgrading real Score-1 findings on systems that do deploy databases/data-at-rest surfaces.


## Phase C calibration follow-ups — Shipped Apr 30, 2026 (branch `fix/ara-calibration`)

Three small MOD rubric-tightening items surfaced by the Apr 30 cross-portfolio scan (`scan-rubric-quality.py`, 2163 MOD + 2978 ARA findings). All shipped together in an uncommitted working-tree edit on top of `cfe3a04`.

- ✅ **C-3 — INF-Q11 rubric rows now carry "application + IaC" framing.**
  Rewrote Scores 1-4. Score 4: *"Full CI/CD automation covering both application code and infrastructure-as-code changes, with test, build, deploy, and automated rollback stages."* Score 3 adds the one-track-automated-other-manual case. Score 2 names "application code and/or IaC changes." Score 1 names "all application and infrastructure deployments are manual scripts or ClickOps." The application+IaC framing now lands in rendered rubric output, not just the question header.

- ✅ **C-6 — MOD SEC-Q5 Score 1/2/3 boundary rewritten.**
  Score 2 had been absorbing 33 repos with mixed maturity — CloudFormation `NoEcho` parameters, SSM Parameter Store for admin passwords, and repos with remaining plaintext alongside some secret management. New rubric:
  - Score 1 = plaintext credentials present anywhere in repo (source, configs, `.env`, `application.properties`, connection strings in IaC without secret references). Score 1 applies even when a secrets manager exists elsewhere.
  - Score 2 = no plaintext but credentials in plain env vars, parameter store without encryption, or CloudFormation `NoEcho` parameters without rotation.
  - Score 3 = Secrets Manager/Vault with rotation on high-risk secrets; some non-critical configs may remain in env vars.
  - Score 4 = all secrets managed with automated rotation.
  Look-for extended with Score 2/3 differentiation signals (`SecureString` vs `String`, `rotation_lambda_arn`, NoEcho backed by Secrets Manager).

- ✅ **C-7 — MOD surface-flag calibration.**
  Added new **Step 1.6: Target-System Surface Detection** (parallels ARA Step 1.5) with five flags derived from Step 1 inventory:
  - `has_persistent_data_store` — DB resources in IaC, self-managed DB in compose/K8s/Helm, or DB driver in source with connection config.
  - `has_at_rest_data_surface` — S3, RDS/Aurora/DynamoDB/DocDB/Neptune/Timestream/ElastiCache, EBS attached to workloads, EFS, managed storage. Implied by persistent_data_store=true.
  - `has_deployed_workload` — deployable compute in IaC, or Dockerfile+deployment manifests. Pure libraries are false.
  - `has_api_surface` — HTTP/gRPC/RPC endpoints, API Gateway, ALB listeners, AppSync. CLI/SDK libraries are false.
  - `has_multi_instance_deployment` — ASG desired>1, K8s replicas>1, ECS desired_count>1, Lambda, serverless.

  Surface gates applied:
  - **INF-Q2** (Managed Databases) requires `has_persistent_data_store`
  - **SEC-Q2** (Encryption at Rest) requires `has_at_rest_data_surface`
  - **INF-Q8** (Backup/Recovery) requires persistent store OR at-rest surface
  - **INF-Q9** (High Availability) requires deployed workload + api/data surface
  - **OPS-Q2** (SLOs) requires api or data surface

  When the gate flag is `false`, the question records as **"Not Evaluated (archetype-N/A)"** rather than defaulting to Score 1. Inline Notes added to INF-Q2 and SEC-Q2 sections. The surface-flag pattern is the MOD-side equivalent of the ARA R1/R6/R8 recalibration — libraries, utilities, and CLI tools stop getting Score 1 "no managed database" / "no encryption at rest" findings when they don't expose those surfaces at all.

**Verification pending:** Post-v5 re-run scan should show INF-Q2 Score 1 concentration drop from 59% and SEC-Q2 Score 1 from 86%, with real data-handling repos (unishop, hapi-fhir, bao-demo Camunda) keeping Score 1/2 where warranted.

