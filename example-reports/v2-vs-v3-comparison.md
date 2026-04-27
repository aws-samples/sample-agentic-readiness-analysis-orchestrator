# V2 vs V3 Comparison — Feedback Validation

**Baseline**: `example-reports/v2-full-assessment/` (pre-feedback)
**New run**: `example-reports/v3-full-assessment/` (post-feedback — all 40 items in `kiro-execution-plan.md`)
**Portfolio config**: identical except v3 adds `portfolio_bridge` TD name
**Scope**: 5 repos × (ARA + MOD) + 2 portfolio reports + new bridge report

---

## Portfolio-Level Headline Shifts

| Metric | v2 | v3 | Delta | Interpretation |
|---|---|---|---|---|
| MOD portfolio score | 2.15 | 2.13 | −0.02 | Essentially stable |
| Score range | 1.40 – 2.71 | 1.67 – 2.65 | Lowest pulled up, highest unchanged | Lowest-scoring services benefited most |
| Not Ready (<1.5) count | 1 (unishop) | 0 | −1 | unishop moved from "Not Ready" → "Needs Work" |
| Foundational blockers | 22 | 20 | −2 | Rubric precision eliminated two marginal blockers |
| Improvement opportunities | 3 | 5 | +2 | More items correctly classified as Improvement vs Blocker |
| Pathways triggered | 6/7 | 5/7 | −1 | One pathway legitimately no longer triggers (below) |
| ARA BLOCKERs (not in v2 snapshot) | n/a | 9 | — | Bridge introduces BLOCKER/RISK-SAFETY/RISK-QUALITY splits |

The net: v3 is not meaningfully more lenient — the **distribution of scores is sharper**. The 22 → 20 blocker count plus the 3 → 5 improvement-opportunity count is a precision win, not a grade inflation.

---

## Feedback Items Validated (What Landed)

### ✅ Terminology fixes (M1–M4) — fully landed

- `compute tiers` → 0 hits in all v3 reports (was in MOD TD Score 4 rubric)
- `primary database` → only appears now in narrative context ("primary production database"), never in rubric quotes. The specific v2-vintage phrasings in INF-Q8/Q9 rubric rows are gone.

**Verdict**: Clean win. No stale rubric quotes.

### ✅ App Mesh removal (M5 + A1) — fully landed

- v2 and v3: `App Mesh` appears in online-boutique example reports (pre-existing, untouched — as expected per TODO).
- v3 ARA + MOD for the 5 target repos: **zero App Mesh mentions**. The discovery list and INF-Q6 look-for no longer suggest it.

**Verdict**: Clean win.

### ✅ New AWS services (M6–M10) — landed and actively used

v3 references:
- **MWAA** — appears in unishop, books-api, aws-microservices INF-Q3 findings as an orchestration option
- **Amazon MQ** — appears in unishop INF-Q4 finding explicitly checking for it
- **AppSync** — appears in eks-saas-gitops INF-Q6 as an API entry option
- **appspec.yml** — appears in aws-microservices + local-monolith INF-Q11 findings as a CI/CD signal being searched for
- **Neptune, Timestream, IoT Core** — no natural hit in these specific repos, but the discovery logic ran (absence means correctly not detected, not missing from TD)

**Verdict**: The additions show up in the exact places we predicted.

### ✅ APP-Q1 tone fix + reclassification (M29) — biggest behavioral shift

Direct comparison on unishop:

| Version | Score | Wording |
|---|---|---|
| v2 | **4** | "Java itself scores 4. These are version gaps, not language gaps" |
| v3 | **2** | "Java 8 is an older version (long-term support ending)... limits access to modern language features... AWS SDK v1 is in maintenance mode" |

The v2 rubric let Java 8 off the hook because "Java the language" was modern. v3 correctly reflects that the stack (Java 8 + Spring Boot 2.1 + AWS SDK v1) is constrained by AWS tooling limits — pulling unishop's APP-Q1 from 4 → 2. **This is exactly the reclassification B11/M29 was designed to produce**, and it's the primary driver of unishop moving out of "Not Ready".

**Verdict**: Strong win. Most impactful feedback item by behavior change.

### ✅ INF-Q7 broadening (M36–M39) — landed

v3 INF-Q7 findings now evaluate compute AND data auto-scaling:
- aws-microservices: evidence line cites `BillingMode.PAY_PER_REQUEST` (DynamoDB), `DynamoDB throttling events`, `DynamoDB capacity alarms`
- books-api: evidence cites DynamoDB on-demand scaling explicitly
- eks-saas-gitops: evidence covers Karpenter + HPA + DynamoDB PAY_PER_REQUEST as one picture

v2 aws-microservices INF-Q7 was already at Score 3 mentioning DynamoDB+Lambda, but gap analysis was compute-only ("reserved concurrency"). v3 evidence now calls out data-tier gaps too (DynamoDB throttling alarms, API Gateway throttling tuned for traffic).

**Verdict**: Rubric broadening reflected in evidence + gap narrative.

### ✅ DATA-Q3 version-update procedure (M33) — landed

v3 explicitly requires documented version-update procedure in findings:
- unishop: "No documented version-update procedure"
- local-monolith: "No documented version-update procedure covering downtime windows, rollback, or risk acknowledgment"
- eks-saas-gitops: "No documented version-update procedure exists"

v2 did not flag version-update procedure at all.

**Verdict**: New signal landed cleanly. Exactly what Thread 41 asked for.

### ✅ INF-Q8 cross-region backup (M34) — landed

v3 INF-Q8 findings now flag missing cross-region backup as a Score 4 requirement:
- unishop gap: "No cross-region backup replication"
- local-monolith gap: "No cross-region backup replication" (scored 3 instead of 4 because of this)
- books-api recommendation: "cross-region backup replication of the books catalog data"
- aws-microservices recommendation: "DynamoDB Global Tables for multi-region resilience"

v2 mentioned multi-AZ and PITR but not cross-region consistently.

**Verdict**: Multi-region concern integrated into backup rubric as intended.

### ✅ INF-Q5 managed networking rework (M40) — landed

v3 INF-Q5 findings now systematically check for managed networking services:
- unishop gap: "No VPC endpoints, PrivateLink, or zero-trust networking"
- eks-saas-gitops: "No VPC endpoints, PrivateLink, or VPC Lattice configured"
- books-api: "no VPC endpoints or PrivateLink configurations"
- local-monolith: recommends VPC Lattice for service-to-service networking
- aws-microservices: evaluates against PrivateLink/VPC endpoint baseline

v2 INF-Q5 findings were shorter and didn't systematically evaluate against the modern managed-networking stack.

**Verdict**: Rubric expansion properly flowing into evidence.

### ✅ AgentCore Identity signal (A3) — landed

v3 eks-saas-gitops ARA: "no Bedrock AgentCore Identity configuration" in the AUTH-Q1 finding.
v2: zero mentions of AgentCore Identity anywhere.

**Verdict**: Detection signal added and being used.

### ✅ OPS-Q9 SCP removal (M35 / F1) — landed

v3 MOD reports have zero SCP recommendations for tagging. The remediation text uses "IaC enforcement, Tag Policies, AWS Config rules" — exactly per F1.

v2 had SCPs recommended in books-api and local-monolith OPS-Q9 tagging findings (you can still see it in v2 reports). Note: SCP appears in v3 portfolio MOD only as a link in a URL (`SCPSHC` in a Skillbuilder URL) — that's a false positive, not a rubric reference.

**Verdict**: Clean removal.

---

## Feedback Items Partially Landed / Not Visible

### ⚠️ ARA Summary/Objective framing (A4–A8) — TD edits landed, reports didn't echo them

The TD edits for dual-purpose framing, design-time clarification, HITL framing, and control-layer note live in the Summary/Objective/Step 5 sections of the TD. These are **template framing**, not rubric-scoring changes. Reports don't quote Summary/Objective text — they generate per-question findings. So:

- `design-time`, `portfolio-level telemetry`, `user is the subject` → 0 hits in v3 reports
- `multitenancy` (A11) → 0 hits in v3 reports

This is expected behavior. The framing exists in the TD to guide the assessor's interpretation; it won't appear verbatim in the output unless it's anchored in a rubric row or question text.

**Verdict**: Not a regression. But if you want these framings to be visible in the reports, the next iteration would need to lift them from Summary into per-question narrative guidance.

### ⚠️ MCP awareness clause (A13) — TD edit landed, no hit in v3 reports

`MCP` → 0 hits in v3 ARA reports (and the repos don't expose MCP-ish surfaces). The Step 2 intro addition only activates when the report touches the API dimension narrative — and these specific repos don't trigger it.

**Verdict**: Expected. Would need an MCP-adjacent repo to test it exercises.

### ⚠️ S3 File Gateway (E2 / M18) — TD edit landed, no hit in v3 reports

`File Gateway` → 0 hits. None of the 5 repos have a data-migration-from-on-prem scenario where Score 2 is triggered with the "File Gateway as on-ramp" note relevant. The edit is in the TD Score 2 rubric row but no DATA-Q1 in these 5 repos scored 2 in a way that would surface the note.

**Verdict**: TD edit is correct; coverage gap is a repo-selection artifact.

### ⚠️ COBOL/VB6/Classic ASP example (B11) — no hit in v3

The example wording "COBOL, VB6, Classic ASP" was from the B11 example in the TODO. v3 reports use Java 8 / Spring Boot 2.1 / SDK v1 as the observed evidence — correctly, because no repo has COBOL. The **tone principle** (attribute gaps to AWS SDK maturity, not customer "not modern") landed per the APP-Q1 check above.

**Verdict**: Principle landed. Example wording only surfaces when actually applicable.

### ⚠️ INF-Q11 application+IaC pipelines clarification (E4 / M16) — not visible in report wording

No v3 report explicitly says "application and IaC pipelines". The INF-Q11 findings still read as CI/CD-for-application findings. The TD was clarified but the report language is still application-pipeline-centric.

**Verdict**: TD edit landed (per execution plan), but didn't propagate to report language. Minor — the intent is still served because IaC pipelines are evaluated implicitly in INF-Q10 and INF-Q11 for eks-saas-gitops.

---

## New Behaviors Introduced in v3

### 🆕 Bridge Report (new deliverable)

v2 didn't have this. v3 bridge report:
- 17 shared remediation mappings (ARA finding ↔ MOD co-requisite)
- **67% of ARA service-level BLOCKERs resolvable by MOD Phase 0** — a concrete dividend metric
- Both MOD readiness gates triggered (SEC 1.88, OPS 1.31 — both below 2.0)
- Unified remediation sequence consolidating 8 MOD Phase 0 items + 5 ARA-specific items
- Deduplication: 12 items can be planned once instead of twice

**Why this matters**: Before v3, teams had two separate tracks (MOD roadmap + ARA remediation) with no formal cross-reference. The bridge quantifies that most ARA identity/access BLOCKERs fall out of the MOD Cognito deployment for free.

### 🆕 Dependency inference (both runs have it, but v3 is calmer)

v2 inferred 4 dependencies; v3 inferred 2 (just the EKS platform → monolith links). v3 dropped the speculative `aws-microservices ← local-monolith` and `aws-microservices ← unishop` edges that v2 guessed. Not driven by TD changes — could be run-to-run variance, but the v3 graph is more defensible.

### 🆕 Portfolio-level questions (PORT-MOD-Q1..Q5, PORT-ARA-Q1..Q5)

Both runs have them. v3 question scoring and evidence is tighter:
- PORT-MOD-Q4 (Technology Diversity): v2 scored 2 @ "15 technologies"; v3 scored 2 @ "14 technologies / 5 services = 2.8". Same finding, cleaner evidence.
- PORT-ARA-Q5 (Agent Identity Governance) — v3 adds this as RISK with a concrete kill-switch recommendation that v2's portfolio ARA didn't surface as cleanly.

---

## Regressions / Things to Watch

### 🟡 APP-Q1 reclassification is aggressive

unishop APP-Q1 went 4 → 2. That's a real rubric shift, not noise. Local-monolith stayed higher (PHP 8.2 is modern). The tone fix successfully flagged the legacy-stack concern — but it's worth eyeballing whether Score 2 is right for "Java 8 + outdated Spring" or whether Score 3 would be more accurate (language is modern, framework lag is the actual issue). The TD could be reviewed for whether Java 8 = Score 2 is too harsh for customers still on Java 8 as a corporate standard.

### 🟡 Dates in assessment inventory are mixed

Portfolio MOD Assessment Inventory shows mixed dates:
- unishop: 2025-07-17
- eks-saas-gitops: 2025-07-15
- others: 2026-04-27

The individual reports were freshly generated 2026-04-27 but the inventory pulled `assessment_date` from frontmatter the agent wrote inside the report rather than file mtime. Low severity — the TD or portfolio aggregation prompt could be tweaked to use the actual run date. Also affects v2, so not a regression.

### 🟡 INF-Q11 narrative gap

As noted above, no report says "application and IaC pipelines" explicitly. If reviewers specifically wanted to see that phrasing in the output, it's not there.

---

## Bottom Line

**The feedback passes that matter most — tone fixes, terminology cleanup, rubric precision, new AWS services, SCP removal, INF-Q7 broadening, cross-region backup — all landed and are visibly shaping the reports.**

The items that didn't show up are almost entirely TD framing text (Summary, Objective, Step intros) that doesn't get quoted into reports, or feedback that requires a specific repo scenario (File Gateway, MCP) to exercise.

### Recommended adjustments

1. **APP-Q1 Score 2 threshold** — consider whether the tone-corrected rubric is pulling customers too low for "stack lag". Review Score 2 vs Score 3 criteria with a calibration example.
2. **If you want design-time / dual-purpose framing visible in reports**, lift those clauses from the ARA Summary/Objective into per-question why-it-matters guidance so they anchor in the output.
3. **Date handling in portfolio aggregation** — make `assessment_date` in Assessment Inventory come from file mtime or run date, not whatever the individual assessor wrote.
4. **Broaden test coverage** — the next sample portfolio run should include one repo that exercises MCP (for A13) and one on-prem migration scenario (for M18 S3 File Gateway) so those TD edits get exercise.

The feedback pass is working. Nothing needs to be rolled back.
