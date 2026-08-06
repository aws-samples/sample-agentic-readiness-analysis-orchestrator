# MOD Output Contract

> **Purpose:** Loaded by the Modernization Readiness Analysis (MOD) TD to emit its four-artifact bundle. Defines the unified severity and category display names, the unified per-finding field set and `mod_metadata` subobject, classification rules and the classification-consistency check, per-repo `pathways[]` emission, the MD report contents, the four-artifact contract, and error handling. This is the machine-readable contract the portfolio aggregator and webapp consume.

---

## Unified Severity and Category Display Names

This TD emits findings in a unified severity vocabulary (High / Medium / Low) and canonical category display names so that MOD findings render in the same webapp tables, filters, and counters as ARA findings. The internal 1–4 score is preserved on every finding under `mod_metadata.internal_score` — it drives pathway triggers and Scoring Notes arithmetic.

#### Unified Severity Mapping

Every MOD finding carries a top-level `severity` field with a value from {High, Medium, Low}. The mapping from the internal 1–4 score is:

| Condition | Unified Severity |
|---|---|
| `internal_score == 1` AND `core_question == true` | High |
| `internal_score == 1` AND `core_question == false` | Medium |
| `internal_score == 2` | Medium |
| `internal_score == 3` | Low |
| `internal_score == 4` | (no finding — passing) |
| N/A / Not Evaluated | (no finding) |

A score of 4 is the "passing" score and MUST NOT emit a finding — the question is recorded only under `evaluations[]`. Similarly, N/A and Not Evaluated (archetype-N/A, extended-not-triggered) SHALL NOT emit findings. The question's 1–4 score still feeds Scoring Notes arithmetic and pathway trigger evaluation regardless of whether a finding was emitted.

The internal score is preserved verbatim in `mod_metadata.internal_score`, the core-question designation in `mod_metadata.core_question`, and the human-readable label ("Not Ready" / "Needs Work" / "Partial") in `mod_metadata.score_label`. See the `mod_metadata` subobject section below.

#### Category Display Names

Every MOD finding carries both a short `category_id` code (the rubric section prefix, used as `question_id` prefix) and a webapp-facing `category` display name. The canonical mapping:

| `category_id` | `category` display name |
|---|---|
| `INF` | Infrastructure & DevOps |
| `APP` | Application Architecture |
| `DATA` | Data Platform |
| `SEC` | Security Baseline |
| `OPS` | Operations & Observability |

Both `category_id` and `category` are REQUIRED fields on every MOD finding. MD and HTML section headers render the display name with the short code in parentheses where it adds clarity (e.g., "Infrastructure & DevOps (INF)"). The portfolio JSON `filter_vocab.categories[]` array carries display names only.

#### DATA-Q* Namespace Collision Note

The short code `DATA` is shared between MOD and the Agentic Readiness Analysis (ARA). MOD `DATA-Q1`..`DATA-Q4` and ARA `DATA-Q1`..`DATA-Q7` are DIFFERENT questions and MUST NOT be conflated. The unique join key across the two analysis types is `(analysis_type, question_id)` — never `question_id` alone. MOD `DATA` disambiguates to display name **"Data Platform"**; ARA `DATA` disambiguates to **"Data Accessibility"**. Every JSON artifact emits `analysis_type` at the root (values `"mod"`, `"ara"`, `"portfolio-mod"`, `"portfolio-ara"`) so the join key is always present.

---

### Unified Per-Finding Field Set and `mod_metadata` Subobject

This section defines the per-finding JSON shape for MOD. It mirrors the ARA TD's per-finding field set — the 12 base fields are identical across ARA and MOD so a single webapp can render both without per-analysis branching — with a MOD-specific `mod_metadata` subobject replacing ARA's `ara_metadata`.

#### Per-Finding Required Fields

Every MOD finding MUST carry these 12 fields:

| Field | Type | Description |
|---|---|---|
| `question_id` | string | MOD rubric question identifier (e.g., `"INF-Q1"`). |
| `category` | string | Webapp-facing category display name (e.g., `"Infrastructure & DevOps"`). |
| `category_id` | string | Rubric short code (e.g., `"INF"`). |
| `title` | string | Short finding title. |
| `description` | string | Finding description. |
| `gap` | string | What is missing or inadequate relative to the rubric. |
| `recommendation` | string | Remediation recommendation. |
| `severity` | enum | `"High"` / `"Medium"` / `"Low"` — unified severity per the table above. |
| `priority` | enum | `"P0"` / `"P1"` / `"P2"` / `"P3"` — static per-question priority. See table below. |
| `effort` | enum | `"High"` / `"Medium"` / `"Low"` — remediation effort estimate. |
| `phase` | integer | `1`–`4` — derived roadmap phase, default. |
| `evidence` | object or null | `{file, lines}` reference to the gap location in the repo. **When the finding is that something is ABSENT, cite where you looked** — `{"file": "<the file or path searched>", "lines": null}` — because absence is evidence (see Notable absences in Discovery). Reserve `null` for the rare finding that is genuinely repo-wide with no representative path to name. `lines` is `null` whenever no specific line range applies. |

All 12 fields are REQUIRED on every emitted finding — missing any one fails the analysis and names the offending `question_id`. Findings are NEVER emitted for questions that resolve to pass (score 4), N/A, Not Evaluated (archetype-N/A), or Not Evaluated (extended-not-triggered); those questions appear only under `evaluations[]`.

#### MOD Metadata Subobject (`mod_metadata`)

Every MOD finding MUST carry a populated `mod_metadata` subobject (emitted as a sibling of the 12 required fields above) that preserves the scoring detail so the full MOD rubric depth stays visible:

| Field | Type | Description |
|---|---|---|
| `internal_score` | integer 1-3 | The 1–4 score that emitted this finding. Values of 1, 2, or 3 only — a score of 4 is the passing score and emits no finding. |
| `score_label` | enum | Human-readable label: `"Not Ready"` (score 1) / `"Needs Work"` (score 2) / `"Partial"` (score 3). Score 4 is "Mature" but does not emit a finding. |
| `archetype_calibrated` | boolean | `true` ONLY for INF-Q3, INF-Q4, APP-Q3, APP-Q4 when service archetype influenced the score. Always `false` on all other questions. When `true`, the MD artifact MUST include prose explaining how the archetype shaped the score. |
| `core_question` | boolean | Mirrors the MOD rubric's core-question designation (see "Core Question Designation Table" below). Drives the severity mapping rule that turns `internal_score == 1` on a core question into a High finding, and the same score on a non-core question into a Medium finding. |

#### Core Question Designation Table (authoritative)

Every MOD question has a static `core_question` value that does NOT change per-repo. This is the authoritative source for the `mod_metadata.core_question` field:

| Question | Core? | Question | Core? |
|---|---|---|---|
| INF-Q1 Managed Compute | ✅ core | DATA-Q1 Unstructured Data Storage | ✅ core |
| INF-Q2 Managed Databases | ✅ core | DATA-Q2 Unified Data Access Layer | non-core |
| INF-Q3 Workflow Orchestration | non-core | DATA-Q3 Database Engine Version and EOL | ✅ core |
| INF-Q4 Async Messaging and Streaming | non-core | DATA-Q4 Stored Procedures and Schema Complexity | ✅ core |
| INF-Q5 Network Security | ✅ core | SEC-Q1 Audit Logging | ✅ core |
| INF-Q6 API Entry Point | non-core | SEC-Q2 Encryption at Rest | ✅ core |
| INF-Q7 Auto-Scaling | non-core | SEC-Q3 API Authentication | non-core |
| INF-Q8 Backup and Recovery | non-core | SEC-Q4 Centralized Identity Integration | non-core |
| INF-Q9 High Availability and Fault Isolation | non-core | SEC-Q5 Secrets Management | ✅ core |
| INF-Q10 Infrastructure as Code Coverage | ✅ core | SEC-Q6 Compute Hardening and Patching | non-core |
| INF-Q11 CI/CD Automation | ✅ core | SEC-Q7 Application Security Pipeline | non-core |
| APP-Q1 Programming Languages | non-core | OPS-Q1 Distributed Tracing | non-core |
| APP-Q2 Monolith vs Microservices | ✅ core | OPS-Q2 SLO Definitions | non-core |
| APP-Q3 Async vs Sync Communication | non-core | OPS-Q3 Business Metrics | non-core |
| APP-Q4 Long-Running Process Handling | non-core | OPS-Q4 Anomaly Detection and Alerting | non-core |
| APP-Q5 API Versioning Strategy | non-core | OPS-Q5 Deployment Strategy | ✅ core |
| APP-Q6 Service Discovery | non-core | OPS-Q6 Integration Testing | ✅ core |
|  |  | OPS-Q7 Incident Response Automation | non-core |
|  |  | OPS-Q8 Observability Ownership | non-core |
|  |  | OPS-Q9 Resource Tagging Governance | non-core |

**Total: 14 core questions, 23 non-core questions** (37 total).

**Derivation rationale** (matches the per-question priority table above):
- All questions with `priority: P1` (the 14 P1 questions) are core.
- All questions with `priority: P2` are non-core.
- Core questions govern whether a score 1 creates a High-severity finding. Non-core questions at score 1 are Medium-severity.
- This table is static — it does NOT depend on per-repo context. The same `(analysis_type, question_id)` pair always yields the same `core_question` value.

**Worked severity mapping examples:**
- `INF-Q1` with score 1 → core=true → **High** finding
- `INF-Q3` with score 1 → core=false → **Medium** finding (non-core score 1 is not a High because INF-Q3 is archetype-calibrated and may score 1 correctly for some archetypes)
- `OPS-Q2` with score 1 → core=false → **Medium** finding (OPS-Q2 has `⚠️ Scoring limitation — external context dependency` noted in the rubric, which is why it's non-core)
- Any question with score 2 → **Medium** finding regardless of core_question

`mod_metadata` preserves scoring detail. The Score Summary table, Scoring Notes arithmetic, pathway trigger logic, and archetype-calibration prose all remain authoritative and unchanged — `mod_metadata` just surfaces the per-finding scoring reasoning in structured JSON so the webapp and the portfolio aggregator can consume it without re-parsing MD.

#### Evaluations Array (`evaluations[]`)

Questions that do NOT produce a finding (score 4 = pass, N/A, Not Evaluated) are recorded in `evaluations[]`. Every one of the 37 question IDs appears in EITHER `findings[]` OR `evaluations[]` — never both, never neither.

| Field | Type | Description |
|---|---|---|
| `question_id` | string | e.g., `"INF-Q1"` |
| `category_id` | string | e.g., `"INF"` |
| `title` | string | Question title (e.g., "Managed Compute") |
| `status` | enum | `"pass"` / `"na"` / `"not_evaluated_archetype"` / `"not_evaluated_surface_flag"` |
| `score` | integer or null | The internal 1-4 score (4 for pass, null for N/A/Not Evaluated) |
| `reason` | string | Why this status was assigned (e.g., "Score 4 — fully managed compute on EKS with Karpenter", "Library repo — INF questions are N/A") |

#### Explicit Forbid: No `pathway_triggers` Field on Findings

MOD findings MUST NOT carry a `pathway_triggers` field (or any equivalent pathway-trigger evidence field) under `mod_metadata` or at any other level of the finding. Pathway trigger evidence lives ONLY on `pathways[]` entries via the `triggering_questions[]` array — see the Per-Repo `pathways[]` Emission section below. This keeps the finding shape aligned with ARA and ensures that the portfolio MOD TD can consume pathway-trigger "why" evidence from a single authoritative location (`pathways[].contributing_repos[].triggering_questions[]`).

#### Per-Question Priority Table

The `priority` field on every MOD finding is STATIC per rubric question — it does not depend on per-repo context. Portfolio aggregation relies on this stability: the same `(analysis_type, question_id)` pair always yields the same `priority`.

**Authoritative source.** When `modernization-readiness-findings.csv` is present in the workspace, its per-question priority column is the authoritative source and overrides the defaults below. When the CSV is absent (current state of the workspace), the defaults in the table below are used.

**Default derivation.** Priority is derived mechanically from core/non-core designation: core questions default to P1, non-core questions default to P2, and the four archetype-calibrated questions (INF-Q3, INF-Q4, APP-Q3, APP-Q4) default to P2 because their scoring is archetype-sensitive rather than uniformly critical. Specifically:

- Core question → **P1**
- Non-core question → **P2**
- Archetype-calibrated question (INF-Q3, INF-Q4, APP-Q3, APP-Q4) → **P2**

Concrete per-question defaults for all 37 MOD questions:

| Question | Priority | Question | Priority |
|---|---|---|---|
| INF-Q1 | P1 | DATA-Q1 | P1 |
| INF-Q2 | P1 | DATA-Q2 | P2 |
| INF-Q3 | P2 | DATA-Q3 | P1 |
| INF-Q4 | P2 | DATA-Q4 | P1 |
| INF-Q5 | P1 | SEC-Q1 | P1 |
| INF-Q6 | P2 | SEC-Q2 | P1 |
| INF-Q7 | P2 | SEC-Q3 | P2 |
| INF-Q8 | P2 | SEC-Q4 | P2 |
| INF-Q9 | P2 | SEC-Q5 | P1 |
| INF-Q10 | P1 | SEC-Q6 | P2 |
| INF-Q11 | P1 | SEC-Q7 | P2 |
| APP-Q1 | P2 | OPS-Q1 | P2 |
| APP-Q2 | P1 | OPS-Q2 | P2 |
| APP-Q3 | P2 | OPS-Q3 | P2 |
| APP-Q4 | P2 | OPS-Q4 | P2 |
| APP-Q5 | P2 | OPS-Q5 | P1 |
| APP-Q6 | P2 | OPS-Q6 | P1 |
|  |  | OPS-Q7 | P2 |
|  |  | OPS-Q8 | P2 |
|  |  | OPS-Q9 | P2 |

(37 rows total — 11 INF + 6 APP + 4 DATA + 7 SEC + 9 OPS.) Per-finding `priority` is static per `question_id` and does not change per-repo, per-portfolio, or per-score. If `modernization-readiness-findings.csv` later lands in the workspace, the CSV's explicit per-question assignments replace these defaults wholesale.

#### Default Phase Mapping from Priority

The default `phase` assignment on a finding derives mechanically from `priority`:

| `priority` | Default `phase` |
|---|---|
| P0 | 1 |
| P1 | 1 |
| P2 | 2 or 3 |
| P3 | 3 or 4 |

Per-repo MOD MAY pin a specific phase within the allowed band based on local remediation dependencies; portfolio MOD MAY further adjust `phase` based on cross-cutting dependencies across the portfolio. The `priority` value itself does NOT change per-repo or per-portfolio — only `phase` may be re-pinned within its allowed band. When `phase` is re-pinned away from the default, the JSON artifact records both the per-repo-adjusted value (as `phase`) and, if applicable, the portfolio-adjusted value under a sibling field.

---

### Classification Rules (MOD) and Classification Consistency Check

The per-repo MOD classification assigns each assessed repository to exactly one of four tiers based on the unified High / Medium counts derived from the severity mapping above. MOD also emits a classification consistency check that ensures the score-based tier (derived from the `overall_score` band) and the count-based tier (derived from High / Medium counts) tell the same story.

MOD classification is deliberately SOFTER than ARA classification on "1 High." ARA gates on agent safety — a single High is a deployment blocker. MOD measures modernization maturity — a single High is typically one modernization gap rather than a deployment blocker. This is documented inline in the MD classification rationale block.

#### Classification Table

| High count | Medium count | Tier | `rule_matched` |
|---|---|---|---|
| 0 | ≤ 1 | Cloud-Native Ready | "0 High, ≤1 Medium → Cloud-Native Ready" |
| 0 | ≥ 2 | Pilot-Ready | "0 High, ≥2 Medium → Pilot-Ready" |
| 1 | any | Pilot-Ready | "1 High → Pilot-Ready" |
| 2–11 | any | Remediation Required | "2-11 High → Remediation Required" |
| ≥ 12 | any | Not Ready | "≥12 High → Not Ready" |

Tier values: {Cloud-Native Ready, Pilot-Ready, Remediation Required, Not Ready}. There is no sub-qualifier for MOD — the safety-concerns sub-qualifier is ARA-only.

The classification object emitted in per-repo MOD JSON:

```json
{
  "tier": "Remediation Required",
  "high_count": 6,
  "medium_count": 4,
  "low_count": 7,
  "rule_matched": "2-11 High → Remediation Required",
  "classification_consistency_check": "consistent"
}
```

#### Per-Category Emission: Three Coexisting Labels

Each entry in the per-repo MOD JSON `categories[]` array MUST carry ALL THREE of the following labels. They coexist — they do NOT replace one another:

| Field | Source | Values |
|---|---|---|
| `numeric_score` | Arithmetic mean of non-N/A non-Not-Evaluated question scores in that category | 1.00–4.00 (or `null` when every question in the category resolves to N/A or Not Evaluated) |
| `score_rating` | Numeric-score band, derived from `numeric_score` using: ≥ 3.5 → Mature, 2.5–3.4 → Partial, 1.5–2.4 → Needs Work, < 1.5 → Not Ready | `"Mature"` / `"Partial"` / `"Needs Work"` / `"Not Ready"` (or `null` when `numeric_score` is `null`) |
| `severity_status` | Severity-count-driven: High ≥ 1 → Critical; else Medium ≥ 1 → Needs Work; else Ready | `"Critical"` / `"Needs Work"` / `"Ready"` |

**Category-level divergence is ALLOWED**. Example: a category whose only finding is a Score-3 (Low-severity) finding has `numeric_score` 3.67, `score_rating` `"Mature"`, and `severity_status` `"Needs Work"`. That is EXPECTED — the numeric-score band still rounds to Mature while the unified severity count flags one Low-severity finding that needs attention. The JSON surfaces both honestly so consumers can reason about each lens independently. **Repo-level divergence between the score-based band and the count-based tier is NOT allowed** — see the consistency check below.

When every question in a category resolves to N/A or Not Evaluated, `numeric_score` and `score_rating` are `null`, `severity_status` is `"Ready"`, and the MD and JSON artifacts MUST include a note that the category was not evaluated.

#### MD-Rendered Classification Rationale

The per-repo MOD MD artifact MUST render a classification rationale paragraph immediately after the classification tier is first stated. The paragraph:

1. States the specific counts that drove the tier (e.g., "This repo has 6 High findings, 4 Medium findings, 7 Low findings.").
2. Names the matched rule (e.g., "2-11 High → Remediation Required").
3. States the MOD classification rule and explicitly contrasts it with the ARA classification rule: ARA's "1 High" is an agent-deployment gate; MOD's "1 High" is typically a single modernization gap and maps to Pilot-Ready instead of Remediation Required.

#### `classification_consistency_check`

Every MOD JSON `classification` object MUST include a `classification_consistency_check` field whose value is either:

- The string `"consistent"` when the score-based tier (derived from `overall_score` band) and the count-based tier (derived from High / Medium counts) tell the same story per the equivalence table below:
  - Score ≥ 3.5 (Mature band) ≡ Cloud-Native Ready
  - Score 2.5–3.4 (Partial band) ≡ Pilot-Ready
  - Score 1.5–2.4 (Needs Work band) ≡ Remediation Required
  - Score < 1.5 (Not Ready band) ≡ Not Ready

- A structured divergence object when the equivalence does NOT hold:
  ```json
  {
    "status": "divergent",
    "score_band": "Partial",
    "count_tier": "Remediation Required",
    "reason": "Score 2.8 yields Partial band but 4 High findings force Remediation Required tier. Surface gating review recommended on INF-Q2, INF-Q10, SEC-Q1, SEC-Q5."
  }
  ```

When `classification_consistency_check.status == "divergent"`, the MOD MD artifact MUST render a clearly-labeled warning block naming the divergence, the underlying score-based band, the count-based tier, and the reason. Repo-level divergence is a RELEASE BLOCKER and MUST be either (a) corrected by fixing surface-gating or scoring, or (b) documented in the divergence object and flagged for the maintainer. Silent divergence is not acceptable.

Category-level divergence between `score_rating` and `severity_status` (described above) is a different phenomenon — it is permitted and does NOT trigger the repo-level `classification_consistency_check` warning.

---

### Per-Repo `pathways[]` Emission

Every per-repo MOD JSON artifact MUST emit a `pathways[]` array with exactly 7 entries — one per canonical pathway. This surfaces the AWS Modernization Pathways Summary Table as a structured JSON surface that the portfolio MOD TD consumes.

#### The 7 Canonical Pathway IDs

Each per-repo MOD JSON MUST emit one `pathways[]` entry per pathway, using these exact `id` values:

- `move-to-cloud-native`
- `move-to-containers`
- `move-to-open-source`
- `move-to-managed-databases`
- `move-to-managed-analytics`
- `move-to-modern-devops`
- `move-to-ai`

The `name` field on each entry carries the human-readable label (e.g., `"Move to Cloud Native"`) matching the Pathway Summary Table in MD.

#### Per-Entry Shape

Every `pathways[]` entry carries:

| Field | Type | Description |
|---|---|---|
| `id` | enum | One of the 7 canonical IDs above. |
| `name` | string | Display name matching the pathway table. |
| `status` | enum | `"Triggered"` / `"Not Triggered"` / `"Not Applicable"`. |
| `priority` | enum or null | `"High"` / `"Medium"` / `"Low"` for Triggered pathways; `null` for Not Triggered or Not Applicable. |
| `effort` | enum or null | `"High"` / `"Medium"` / `"Low"` for Triggered pathways; `null` for Not Triggered or Not Applicable. |
| `key_trigger_criteria` | string | Prose describing the pathway's trigger condition from Step 7 (e.g., "APP-Q2 < 3 OR INF-Q1 < 3 OR APP-Q3 < 3 OR APP-Q4 < 3"). For Not Applicable pathways, this field states WHY the pathway does not apply to the repo's `repo_type`. |
| `triggering_questions[]` | array | Tuples of `{question_id, score, note?}` identifying the questions consulted. See rules below. |
| `detail` | object or null | Structured detail for Triggered pathways (AWS services, learning materials, immediate actions); `null` for Not Triggered or Not Applicable. |
| `not_triggered_reason` | string, optional | Prose explanation; present on Not Triggered pathways when `triggering_questions[]` alone does not convey the reason. |

#### Status Rules

- **`"Triggered"`** — At least one rubric question named in the pathway's trigger condition (Step 7 above) scored below its threshold after surface-gating and archetype-calibration were applied. The `triggering_questions[]` array MUST be non-empty and MUST contain ONLY `(question_id, score)` tuples whose `score < 3` AND whose `question_id` belongs to the pathway's trigger set (for pathways whose triggers are phrased as `"QUESTION < 3"`). This matches the Step 7 trigger condition exactly — the JSON surfaces the consulted questions as structured data without altering the trigger logic.

- **`"Not Triggered"`** — All rubric questions in the pathway's trigger set scored at or above their threshold (e.g., score ≥ 3), OR the contextual guard from the Pathway Summary Table blocked the trigger (e.g., "Must be EC2/VM-based" for Move to Containers when the workload is already on Lambda/Fargate/ECS). The `triggering_questions[]` array carries the consulted questions with a per-question `note` explaining why each did NOT fire (e.g., `{"question_id": "INF-Q1", "score": 3, "note": "INF-Q1 = 3 meets threshold; pathway not needed"}`). For guard-blocked pathways, a pathway-level `not_triggered_reason` field explains the guard (e.g., `"not_triggered_reason": "Workload already runs on Lambda/Fargate/ECS; container pathway does not apply"`).

- **`"Not Applicable"`** — The pathway does not apply to the repo's `repo_type` (e.g., "Move to Containers" is N/A for a `library` repo because there is no deployable workload). The `key_trigger_criteria` field MUST carry the prose reason (e.g., `"Not applicable — repo_type is 'library' and the pathway requires a deployable workload"`). The `triggering_questions[]` array MAY be empty.

For every pathway with `status == "Triggered"`, the per-repo MOD MD artifact MUST emit a Pathway Detail subsection containing the content specified in Step 7's "When Triggered, Include in Pathway Detail Section" guidance. The corresponding `pathways[].detail` JSON object carries the structured fields (triggered_questions, recommended AWS services, immediate actions, learning materials) so that the portfolio MOD TD can aggregate pathway detail content from JSON alone.

#### Surface-Gating Discipline

Surface flags (`has_persistent_data_store`, `has_at_rest_data_surface`, `has_deployed_workload`, `has_api_surface`, `has_multi_instance_deployment`, `has_iac_provisioning_aws_resources` — see Step 1.6) MUST be applied BEFORE pathway evaluation. If a surface flag is `false` for a question that would otherwise fire a pathway (e.g., DATA-Q3 < 3 would fire Move to Managed Databases, but `has_persistent_data_store == false` means DATA-Q3 was recorded as Not Evaluated), the question does NOT count toward pathway triggering. This prevents a pathway from firing on a question that was not actually evaluated.

#### Key Trigger Conditions Reference

The per-pathway trigger conditions used to populate `triggering_questions[]` come from the Pathway Summary Table (Step 7) unchanged. The canonical trigger logic is defined in Step 7.1 through 7.7 above; the table below is a quick reference:

| `id` | Primary Trigger | Supporting Triggers (strengthen, not required) | Contextual Guard |
|---|---|---|---|
| `move-to-cloud-native` | APP-Q2 < 3 | At least one of INF-Q1 < 3, APP-Q3 < 3, APP-Q4 < 3 must also be true | — |
| `move-to-containers` | INF-Q1 < 3 AND no container definitions found | — | SHALL NOT trigger if compute is already Lambda/Fargate/ECS |
| `move-to-open-source` | DATA-Q4 < 3 | Commercial DB engines detected in INF-Q2 finding | — |
| `move-to-managed-databases` | INF-Q2 < 3 | DATA-Q3 < 3 (strengthens, not required) | — |
| `move-to-managed-analytics` | INF-Q4 < 3 | Data source sprawl with no unified access layer (DATA-Q2 finding) | Evidence of data processing workloads must exist |
| `move-to-modern-devops` | INF-Q10 < 3 OR INF-Q11 < 3 | OPS-Q5 < 3, OPS-Q6 < 3 (strengthen, not required) | — |
| `move-to-ai` | No AI/agent frameworks, no vector DB, no RAG, no agent eval framework | — | Requires AI/agent/LLM intent in portfolio or service context |

**Primary vs Supporting:** The trigger logic (Step 7.1–7.7) uses a Primary + Supporting model. A pathway is Triggered ONLY when the Primary condition is met. Supporting conditions strengthen the case (inform the Pathway Detail section) but do NOT on their own trigger a pathway. The `triggering_questions[]` array MUST include the Primary question that triggered the pathway plus any Supporting questions whose scores also scored below threshold.

The `triggering_questions[]` array is the structured surface of the "which questions fired, at what scores, why" information that the Pathway Detail section describes in prose — this information must be visible every time a pathway appears (per-repo, per-repo roll-up in portfolio `repositories[].pathways_triggered[]`, and portfolio top-level `pathways[]`).

---

### MD Report Contents

#### MD Sections

The following content MUST be retained in every per-repo MOD MD report:

- **Overall Score line** rendered in the MD metadata block as `Overall Score: X.XX / 4.0` using the repo-level numeric score. Preserved as a first-class field in JSON under `overall_score`.
- **Score Summary table** — per-category numeric scores with the ✅ Mature / 🟡 Partial / 🟠 Needs Work / ❌ Not Ready emoji rating (the `score_rating` label). Rendered unchanged.
- **Scoring Notes** arithmetic breakdown (e.g., `"INF: (3+1+2+2+1+2+1+2+2+2+2) / 11 = 20/11 = 1.82"`) — preserved in MD. JSON does NOT need to carry Scoring Notes because the final numeric scores are already in `categories[].numeric_score`.
- **Top 5 Gaps** table — rendered in MD with columns `#`, `Question`, `Score`, `Gap`, `Impact`. JSON carries the same data under `top_gaps[]`.
- **Decomposition Strategy** conditional section (fires when APP-Q2 < 3) — rendered in MD including the four approach options (strengthen as modular monolith, Strangler Fig parallel track, conditional/adaptive, big-bang with recommendation against), pattern recommendations (Anti-corruption Layer, Saga, Event Sourcing, Hexagonal Architecture), and level-of-effort estimates. JSON carries a structured `decomposition_strategy` object when the condition fires, `null` otherwise.
- **Archetype Justification** prose — rendered in the MD metadata block. For the four archetype-calibrated questions (INF-Q3, INF-Q4, APP-Q3, APP-Q4), MD prose MUST explain how the detected or supplied archetype shaped the score whenever `mod_metadata.archetype_calibrated == true`.
- **AWS Modernization Pathways** Summary Table with status/priority/effort/Key Trigger Criteria columns, AND Pathway Detail subsections for each Triggered pathway. See the Per-Repo `pathways[]` Emission section for the JSON surface.
- **Aggregate Evidence Index** at the end of the report. JSON consumers can re-derive this section from the union of `findings[].evidence` across all findings.
- **Surface Flags block** with six boolean flags and rationale — rendered in the MD metadata block and in JSON under `metadata.surface_flags`.

The MD artifact renders the following inline annotations alongside the content above:

- Per-finding unified severity badges ("High" / "Medium" / "Low") next to the score label.
- Classification tier (Cloud-Native Ready / Pilot-Ready / Remediation Required / Not Ready) with the matched-rule annotation, rendered after the Overall Score line.
- Per-finding `priority`, `effort`, `phase` values in the finding header block.
- Category `severity_status` (Ready / Needs Work / Critical) in the Score Summary table as a new column alongside the `score_rating`.
- Classification-consistency warning block rendered immediately after the classification tier WHEN `classification_consistency_check.status == "divergent"`.

---

### Four-Artifact Output Contract (MOD)

Every per-repo MOD analysis emits four artifacts: three report artifacts plus a metadata sidecar. This mirrors the ARA four-artifact contract with MOD-specific filenames and a MOD-specific HTML visual contract.

#### Artifacts

| Artifact | Filename | Purpose |
|---|---|---|
| Markdown report | `{repo}-mod-report.md` | Richest-prose artifact. Renders every narrative section (Overall Score, Score Summary table, Scoring Notes arithmetic, Top 5 Gaps, Decomposition Strategy, Archetype Justification, AWS Modernization Pathways summary and detail subsections, aggregate Evidence Index). |
| JSON report | `{repo}-mod-report.json` | **Canonical machine-readable contract.** Consumed by the webapp and the portfolio MOD TD. Every semantic field (findings, classification, categories with all three of `numeric_score` / `score_rating` / `severity_status`, `pathways[]` covering all 7 pathways, `overall_score`, `top_gaps[]`, `decomposition_strategy`, `metadata` including surface flags and archetype justification) is present. |
| HTML report | `{repo}-mod-report.html` | Single self-contained HTML file (no external asset fetches at render time). Renders a subset of the JSON. Tab order: **stats → tech stack → findings → roadmap → programs**. Visual contract defined inline below. |
| Metadata sidecar | `{repo}-mod-report.metadata.json` | Tiny JSON file carrying version compatibility data. Read by downstream consumers before consuming the main JSON. |

The JSON artifact is the canonical contract. If any artifacts disagree on a field, JSON wins.

#### Metadata Sidecar Fields

The sidecar carries the minimum fields required for version compatibility checks:

```json
{
  "analysis_type": "mod",
  "analysis_date": "2026-04-30",
  "td_version": "modernization-readiness-analysis"
}
```

These same fields are redundantly embedded at the root of the main JSON under `metadata` so that consumers which skip the sidecar still have direct access.

#### HTML Visual Contract

The per-repo MOD HTML artifact is a single self-contained HTML file. The tab order matches the webapp and the ARA HTML: **stats → tech stack → findings → roadmap → programs**.

The full visual contract is defined inline below — do NOT reference external files. The HTML renders a subset of the JSON artifact.

- Header title (`{repo_name} - Modernization Readiness Analysis Report`) and subtitle line (`{date} · {language} · {loc} LOC · Portfolio: {portfolio_name}`).
- Executive Summary prose block with four subsections (Repository Status, Key Findings, Remediation Plan, Recommended Actions) and the emoji + tier mapping: 🟢 Cloud-Native Ready / 🟡 Pilot-Ready / 🟠 Remediation Required (rendered with the "Significant Modernization Required" prose label) / 🔴 Not Ready.
- Stats card row (4 cards): Total Findings, High Severity, Medium Severity, Low Severity. MOD KEEPS the Low Severity card (ARA omits Low per ARA convention).
- Technology Stack table with Language / Lines of Code / Framework / Priority rows.
- **Category-by-Category Breakdown table** with status values `Ready` (green), `Needs Work` (yellow/orange), `Critical` (red). This is the MOD convention — ARA uses `Ready` / `Needs Work` / `Blocked` instead.
- **Detailed Findings cards** — simpler than ARA. Each card has `{question_id}: {title}` with a severity badge (uppercase `HIGH` / `MEDIUM` / `LOW`), a `Category:` line, a `FINDING` subsection with the finding description, and a `RECOMMENDATION` subsection. There is NO `GAP` subsection on MOD cards (ARA has one; MOD's gap description is absorbed into the finding description). Findings are ordered severity-descending (High → Medium → Low) then by category order (INF → APP → DATA → SEC → OPS).
- Modernization Recommendation footer block (emoji-headlined with top-3 High-severity recommendations).
- Footer line (`Generated by AWS Transform · Modernization Readiness Analysis Report`).

**HTML-escaping discipline.** Every data value rendered in HTML originates from the JSON artifact (MD prose is NOT part of the HTML round-trip contract). All attacker-controlled strings MUST be HTML-escaped before embedding: repo names, evidence file paths, finding titles, finding descriptions, recommendation text, pathway names, and any other string that originates from repository content or from free-text fields in `additionalPlanContext`. Escape `<`, `>`, `&`, `"`, `'` at render time. This is the same escaping discipline applied to the ARA HTML artifact.

#### Slug Derivation

The `{repo-name}` placeholder in artifact filenames refers to the **slug**, not the filesystem basename. The slug is derived as follows:

```
slug = lowercase(repo.name)
       with any character not in [a-z0-9_-] replaced by '-'
```

When this TD is invoked via the orchestrator, the slug source is the `name` field of the repository entry in `portfolio-config.yaml`. When invoked manually, the slug source is provided implicitly via the working directory's `additionalPlanContext` or, in absence, the repository's directory name normalized by the rule above. **Always derive from the configured name, not the on-disk basename** — they can mismatch (e.g., a `MonoToMicroLegacy` directory configured as `unishop-monolith`).

#### Artifact Layout

```
{portfolio-or-repo}/
└── services/
    └── {repo-name}/
        └── modernization-readiness-analysis/
            ├── {repo-name}-mod-report.md
            ├── {repo-name}-mod-report.json
            ├── {repo-name}-mod-report.html
            └── {repo-name}-mod-report.metadata.json
```

---

## Error Handling

The TD is explicit about failure modes — no defensive inference, no silent skips. Failures name the offending element (question_id, file path, field) so assessors can remediate.

### Required-Field Failure

IF any of the 12 required per-finding fields is absent from an emitted finding, THEN the analysis SHALL fail, naming:
- The `question_id` of the offending finding
- The specific missing field

Example failure message: `"Analysis failed: finding for INF-Q1 is missing required field 'recommendation'. All 12 per-finding fields are REQUIRED."`

### N/A / Not Evaluated Leak

IF a finding is emitted for a question whose resolution was N/A or Not Evaluated, THEN the analysis SHALL fail, naming the `question_id` and the resolution status that should have been recorded in `evaluations[]` instead.

Example: `"Analysis failed: finding emitted for INF-Q2 but the question resolved to Not Evaluated (no persistent data store, has_persistent_data_store=false). N/A / Not Evaluated resolutions MUST be recorded in evaluations[] only."`

### MOD Archetype Calibration Without Justification

IF a MOD finding carries `mod_metadata.archetype_calibrated: true` but the MD artifact does NOT contain prose explaining how the archetype shaped the score, THEN the analysis SHALL fail naming the `question_id`.

### MOD Classification Divergence

IF the repo-level score-based band (derived from `overall_score`) and the count-based classification tier (derived from High / Medium counts) diverge under the equivalence table in the Classification section, THEN the TD SHALL EITHER:
1. Correct the scoring by re-applying surface-gating and archetype-calibration rules to eliminate the divergence, OR
2. Emit `classification.classification_consistency_check` as a structured `{status: "divergent", score_band, count_tier, reason}` object AND render a clearly-labeled warning block in the MD artifact naming the divergence, score_band, count_tier, and reason.

Silent divergence is NOT acceptable — repo-level divergence is a release blocker unless explicitly documented.
