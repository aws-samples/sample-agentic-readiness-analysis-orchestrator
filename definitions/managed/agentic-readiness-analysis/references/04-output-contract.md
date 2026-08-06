# ARA Output Contract

> **Purpose:** Loaded by the Agentic Readiness Analysis (ARA) TD to emit its four-artifact bundle. Defines the unified per-finding field set, the `ara_metadata` subobject, the `evaluations[]` array, classification rules, the four-artifact contract, the HTML visual contract, and error handling. This is the machine-readable contract the portfolio aggregator and webapp consume.

---

## Unified Per-Finding Field Set and `ara_metadata` Subobject

Every ARA finding carries a unified per-finding field set plus a required `ara_metadata` subobject so that ARA JSON can be consumed side-by-side with MOD JSON by a single webapp and portfolio aggregator.

### Per-Finding Required Fields

Every ARA finding MUST carry these 12 fields:

| Field | Type | Description |
|---|---|---|
| `question_id` | string | Rubric question identifier (e.g., `"AUTH-Q1"`). |
| `category` | string | Webapp-facing category display name (e.g., `"Authentication & Authorization"`). |
| `category_id` | string | Rubric short code (e.g., `"AUTH"`). |
| `title` | string | Short finding title. |
| `description` | string | Finding description. |
| `gap` | string | What's missing or incorrect. |
| `recommendation` | string | Remediation recommendation. |
| `severity` | enum | `"High"` / `"Medium"` / `"Low"` — unified severity. |
| `priority` | enum | `"P0"` / `"P1"` / `"P2"` / `"P3"` — per-question priority. See table below. |
| `effort` | enum | `"High"` / `"Medium"` / `"Low"` — remediation effort estimate. |
| `phase` | integer | `1`–`4` — derived roadmap phase. |
| `evidence` | object or null | `{file: string, lines: string}` reference to the gap location (e.g., `{"file": "src/auth.ts", "lines": "42-58"}`). `lines` is a string range like `"12-15"`, a single line like `"42"`, or `null` when no specific line range applies. **When the finding is that something is ABSENT, cite where you looked** — `{"file": "package.json", "lines": null}` for a missing dependency, `{"file": "README.md", "lines": null}` when the repo documents the gap — because absence is evidence (see Notable absences in Discovery). Reserve `null` for the rare finding that is genuinely repo-wide with no representative path to name. |

All 12 fields are REQUIRED on every emitted finding — missing any one fails the analysis and names the offending `question_id`. Findings are never emitted for questions that resolve to pass, N/A, Not Evaluated (extended), or any other non-finding outcome; those questions appear only under `evaluations[]`.

### ARA Metadata Subobject (`ara_metadata`)

Every ARA finding MUST carry a populated `ara_metadata` subobject that preserves the rubric depth and the conditional-resolution reasoning produced in Steps 2–9. The subobject is emitted as a sibling field to the 12 required fields above.

| Field | Type | Presence | Description |
|---|---|---|---|
| `native_severity` | enum | always | `"BLOCKER"` / `"RISK-SAFETY"` / `"RISK-QUALITY"` / `"INFO"` — the native ARA severity. |
| `safety_impact` | boolean | always | `true` for RISK-SAFETY findings and BLOCKERs that are agent-safety hazards; `false` for RISK-QUALITY and INFO. |
| `conditional_resolution` | string | conditional BLOCKERs only | Prose reasoning that resolved the conditional severity for this repo. |
| `agent_scope` | enum | conditional BLOCKERs only | `"read-only"` / `"write-enabled"` — the scope value that drove the resolution. |
| `resolution_reasoning` | string | conditional BLOCKERs only | Prose explaining why the finding was gated under this scope. |
| `remediation_timeline` | string | optional (RISK findings) | e.g., `"60–90 days"`. |
| `compensating_controls` | string[] | optional | Compensating-controls list. |
| `blocker_remediation` | object | optional (BLOCKER findings) | `{immediate, target_state, estimated_effort, dependencies[]}`. |
| `data_q1_subchecks` | object | only when `question_id == "DATA-Q1"` | B1/B2/B3 sub-check reasoning. |

The five conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2) MUST carry the `conditional_resolution`, `agent_scope`, and `resolution_reasoning` trio. DATA-Q1 additionally carries `data_q1_subchecks` with `{b1, b2, b3}`, each having `{fired, severity, reasoning}`. The overall DATA-Q1 `severity` is the unified mapping of the highest sub-check that fires.

`ara_metadata` preserves rubric detail. The classification tier and count rules in the Summary and Report Template sections remain authoritative. `native_severity` is the join key back to BLOCKER / RISK-SAFETY / RISK-QUALITY / INFO counts.

### Evaluations Array (`evaluations[]`)

Questions that do NOT produce a finding (pass, N/A, Not Evaluated) are recorded in `evaluations[]`. Every one of the 43 question IDs appears in EITHER `findings[]` OR `evaluations[]` — never both, never neither.

| Field | Type | Description |
|---|---|---|
| `question_id` | string | e.g., `"AUTH-Q1"` |
| `category_id` | string | e.g., `"AUTH"` |
| `title` | string | Question title (e.g., "Machine Identity Authentication") |
| `status` | enum | `"pass"` / `"na"` / `"not_evaluated_extended"` / `"not_evaluated_archetype"` |
| `reason` | string | Why this status was assigned (e.g., "Infrastructure-only repo — API questions are N/A", "Extended question not triggered — no persistent state") |

### Remediation Roadmap (`remediation_roadmap`)

| Field | Type | Description |
|---|---|---|
| `phases` | integer[] | `[1, 2, 3]` — the phases used in this report |
| `items[]` | object[] | Per-phase remediation items |
| `items[].phase` | integer | 1, 2, or 3 |
| `items[].phase_name` | string | "Blockers", "Safety", or "Quality" |
| `items[].findings` | string[] | Array of `question_id` values in this phase |
| `items[].summary` | string | 1-2 sentence description of the phase focus |

### Recommended Actions (`recommended_actions[]`)

| Field | Type | Description |
|---|---|---|
| `action` | string | Short action title (e.g., "Deploy centralized identity provider") |
| `question_ids` | string[] | Related finding question IDs |
| `priority` | enum | `"P0"` / `"P1"` / `"P2"` / `"P3"` |
| `effort` | enum | `"High"` / `"Medium"` / `"Low"` |
| `rationale` | string | Why this action is recommended |

### Per-Question Priority Table

The `priority` field on every finding is STATIC per rubric question — it does not depend on per-repo context. Portfolio aggregation relies on this stability: the same `(analysis_type, question_id)` pair always yields the same `priority`. The native severity tier provides a baseline, but individual question priorities are hand-tuned to reflect operational impact (e.g., scope-calibrated questions that resolve to INFO under read-only scope receive lower priority than their tier baseline; questions with high remediation dependency on other findings may be elevated). The concrete per-question table below is authoritative — use it directly rather than deriving from severity tier:

| ARA native severity tier | Default per-question priority |
|---|---|
| Unconditional BLOCKER | P0 |
| Conditional BLOCKER (resolves as BLOCKER under write-enabled scope) | P0 |
| RISK-SAFETY | P1 |
| RISK-QUALITY | P2 |
| INFO | P3 |

Concrete per-question assignments for all 43 ARA questions:

| Question | Priority | Question | Priority |
|---|---|---|---|
| API-Q1 | P0 | DATA-Q1 | P0 |
| API-Q2 | P2 | DATA-Q2 | P1 |
| API-Q3 | P2 | DATA-Q3 | P2 |
| API-Q4 | P1 | DATA-Q4 | P2 |
| API-Q5 | P3 | DATA-Q5 | P2 |
| API-Q6 | P2 | DATA-Q6 | P1 |
| API-Q7 | P2 | DATA-Q7 | P3 |
| API-Q8 | P3 | DISC-Q1 | P2 |
| AUTH-Q1 | P0 | DISC-Q2 | P3 |
| AUTH-Q2 | P1 | DISC-Q3 | P3 |
| AUTH-Q3 | P1 | OBS-Q1 | P2 |
| AUTH-Q4 | P2 | OBS-Q2 | P2 |
| AUTH-Q5 | P2 | OBS-Q3 | P3 |
| AUTH-Q6 | P1 | ENG-Q1 | P2 |
| AUTH-Q7 | P1 | ENG-Q2 | P2 |
| STATE-Q1 | P0 | ENG-Q3 | P2 |
| STATE-Q2 | P2 | ENG-Q4 | P3 |
| STATE-Q3 | P1 | ENG-Q5 | P2 |
| STATE-Q4 | P1 | HITL-Q1 | P1 |
| STATE-Q5 | P1 | HITL-Q2 | P1 |
| STATE-Q6 | P2 | HITL-Q3 | P2 |
| STATE-Q7 | P2 | | |

The conditional BLOCKERs are distributed across P0 and P1 in the table above (DATA-Q1 and STATE-Q1 at P0; API-Q4, AUTH-Q6, DATA-Q2 at P1). Per-finding `priority` is static per `question_id` — the ARA native tier still drives classification counts through `ara_metadata.native_severity`; `priority` is a separate, static-per-question field that does not change with `agent_scope` or per-repo resolution.

The default `phase` assignment derives mechanically from `priority`: P0 → Phase 1, P1 → Phase 1, P2 → Phase 2 or 3, P3 → Phase 3 or 4. Per-repo ARA MAY pin a specific phase within the allowed band based on remediation dependencies; portfolio TDs MAY further adjust `phase` based on cross-cutting dependencies across the portfolio. The `priority` value itself does not change per-repo or per-portfolio.

## Classification Rules

The per-repo ARA classification is a named roll-up of the Readiness Profile (Summary section, "Readiness Profile Determination" in the Report Template). The classification uses `blocker_count` and `risk_safety_count` derived from the severity counts — it does NOT use `medium_count`. This guarantees that the Readiness Profile and the classification tier always agree on the same repo.

### Classification Table

| `blocker_count` | `risk_safety_count` | Tier | Sub-qualifier | Readiness Profile | `rule_matched` |
|---|---|---|---|---|---|
| 0 | 0 | Agent-Ready | none | Agent-Ready | "0 BLOCKER, 0 RISK-SAFETY → Agent-Ready" |
| 0 | 1 or 2 | Pilot-Ready | none | Pilot-Ready | "0 BLOCKER, 1-2 RISK-SAFETY → Pilot-Ready" |
| 0 | ≥ 3 | Pilot-Ready | "Pilot-Ready (Safety Concerns)" | Pilot-Ready (Safety Concerns) | "0 BLOCKER, ≥3 RISK-SAFETY → Pilot-Ready (Safety Concerns)" |
| 1 or 2 | any | Remediation Required | none | Remediation Required | "1-2 BLOCKER → Remediation Required" |
| ≥ 3 | any | Not Agent-Integrable | none | Not Agent-Integrable | "≥3 BLOCKER → Not Agent-Integrable" |

Tier values: {Agent-Ready, Pilot-Ready, Remediation Required, Not Agent-Integrable}. Sub-qualifier is ONLY "Pilot-Ready (Safety Concerns)" and ONLY applied when tier is Pilot-Ready AND `risk_safety_count` ≥ 3. RISK-QUALITY count has no effect on classification — it is reported but does not change the tier.

The classification object emitted in JSON:

```json
{
  "tier": "Pilot-Ready",
  "sub_qualifier": "Pilot-Ready (Safety Concerns)",
  "blocker_count": 0,
  "risk_safety_count": 5,
  "risk_quality_count": 7,
  "info_count": 3,
  "high_count": 0,
  "medium_count": 12,
  "low_count": 3,
  "rule_matched": "0 BLOCKER, ≥3 RISK-SAFETY → Pilot-Ready (Safety Concerns)"
}
```

The `high_count`, `medium_count`, and `low_count` fields represent the unified severity counts (BLOCKER→High, RISK-SAFETY+RISK-QUALITY→Medium, INFO→Low when emitted). They are informational — they feed the webapp filter chips — but do NOT drive classification. Only `blocker_count` and `risk_safety_count` do.

### MD-Rendered Classification Rationale

The per-repo ARA MD artifact MUST render a classification rationale paragraph immediately after the classification tier is first stated. The paragraph:
1. States the specific counts that drove the tier (e.g., "This repo has 0 BLOCKER findings and 5 RISK-SAFETY findings").
2. Names the matched rule (e.g., "0 BLOCKER, ≥3 RISK-SAFETY → Pilot-Ready (Safety Concerns)") — the exact string from the `rule_matched` column of the classification table.
3. States the classification tier alongside the Readiness Profile (they are a named roll-up of the same severity counts).

### Conditional BLOCKER Preservation

The five conditional BLOCKER questions (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2) use conditional-severity resolution. The `ara_metadata.conditional_resolution`, `ara_metadata.agent_scope`, and `ara_metadata.resolution_reasoning` fields surface the reasoning in JSON:

- `conditional_resolution`: Free-text prose that describes which native severity was assigned (e.g., "Resolved to BLOCKER: agent_scope=write-enabled AND no transaction scope").
- `agent_scope`: The `read-only` or `write-enabled` value that drove the resolution (sourced from `additionalPlanContext.agent_scope`).
- `resolution_reasoning`: Free-text prose explaining WHY the resolution was applied to this repo (e.g., "DATA-Q1 B1 fired because agent-facing APIs return credentials unmasked in HostConfigResource.cs").

The conditional-BLOCKER resolution logic is defined in Steps 2–9 of the analysis process; the JSON fields above surface that reasoning in a structured form.

## Four-Artifact Output Contract

Every per-repo ARA analysis emits four artifacts: three report artifacts plus a metadata sidecar.

### Artifacts

| Artifact | Filename | Purpose |
|---|---|---|
| Markdown report | `{repo}-ara-report.md` | Richest-prose artifact. Carries every rubric narrative (rubric quotes, compensating-control discussion, BLOCKER Remediation blocks, Archetype Justification, etc.). |
| JSON report | `{repo}-ara-report.json` | **Canonical machine-readable contract.** Consumed by webapp and portfolio TD. Every semantic field (findings, classification, categories, metadata, surface flags) is present. |
| HTML report | `{repo}-ara-report.html` | Single self-contained HTML file. Renders a subset of JSON. Tab order: stats → tech stack → findings → roadmap → programs. Visual contract defined inline below. |
| Metadata sidecar | `{repo}-ara-report.metadata.json` | Tiny JSON file carrying version compatibility data. Read by downstream consumers before consuming the main JSON. |

The JSON artifact is the canonical contract. If any artifacts disagree on a field, JSON wins.

### Metadata Sidecar Fields

The sidecar carries minimum fields for version compatibility checks:

```json
{
  "analysis_type": "ara",
  "analysis_date": "2026-04-30",
  "td_version": "agentic-readiness-analysis"
}
```

These same fields are redundantly embedded at the root of the main JSON under `metadata` (so consumers that skip the sidecar still have access).

### HTML Visual Contract

The per-repo ARA HTML artifact is a single self-contained HTML file (no external asset fetches at render time). The tab order matches the webapp: **stats → tech stack → findings → roadmap → programs**.

The full visual contract is defined inline below — do NOT reference external files. Every field rendered in HTML originates from the JSON artifact; MD prose is NOT part of the HTML round-trip contract. All attacker-controlled strings (repo names, evidence file paths, finding titles, descriptions, pathway names) MUST be HTML-escaped before embedding.

#### HTML Structure and Layout

**Header:**
- Title: `{repo_name} - Agentic Readiness Analysis Report`
- Subtitle line: `{date} · {language} · {loc} LOC · Portfolio: {portfolio_name}`

**Executive Summary:**

Prose paragraph: what the report evaluates, which eight dimensions are examined (API Surface, Authentication & Authorization, State Management, Human-in-the-Loop, Data Accessibility, Discovery & Documentation, Observability, Engineering Maturity).

**Overall Analysis:** `{emoji} {tier_label}` — classification tier with emoji mapping:
- 🟢 Agent-Ready
- 🟡 Pilot-Ready
- 🟠 Remediation Required (rendered as "Significant Remediation Required")
- 🚫 Not Agent-Integrable (rendered as "Not Agent-Integrable - Defer or Descope")

**Quick Stats:** Total Findings: N, By Severity: X High, Y Medium, Z Low, Estimated Remediation: {window}

**Stats Card Row** (4 cards):

| Card | Value source | Subtitle |
|---|---|---|
| Total Findings | `counts.total` | Across all dimensions |
| High Severity | `counts.high` | Critical findings |
| Medium Severity | `counts.medium` | Important findings |
| Low Severity | `counts.low` | Minor findings |

**Repository Details — Technology Stack table:**

| Attribute | Value |
|---|---|
| Language | `metadata.tech_stack.language` |
| Lines of Code | `metadata.tech_stack.loc` |
| Framework | `metadata.tech_stack.framework` |
| Architecture | `metadata.tech_stack.architecture` |

**Findings by Dimension table:**

| Dimension | Total Findings | High Severity | Medium Severity | Low Severity | Status |
|---|---|---|---|---|---|
| API Surface | N | X | Y | Z | Blocked / Needs Work / Ready |
| Authentication & Authorization | N | X | Y | Z | status |
| State Management | N | X | Y | Z | status |
| Human-in-the-Loop | N | X | Y | Z | status |
| Data Accessibility | N | X | Y | Z | status |
| Discovery & Documentation | N | X | Y | Z | status |
| Observability | N | X | Y | Z | status |
| Engineering Maturity | N | X | Y | Z | status |

Status values: `Ready` (green), `Needs Work` (yellow), `Blocked` (red). The dimension order matches the 8-section rubric order from the Summary section (API → AUTH → STATE → HITL → DATA → DISC → OBS → ENG).

**Detailed Findings** — per-finding card structure:

```
{question_id}: {title}          [severity badge]
Section: {section_short_code}

FINDING
{finding_description}

GAP
{gap}

RECOMMENDATION
{recommendation}

Effort: {effort} ({timeline_window})
File: {evidence.file}
Lines: {evidence.lines}
```

Ordered by severity (High → Medium → Low) then by section order (AUTH → API → STATE → DATA → OBS → ENG).

**Remediation Roadmap table:**

| Phase | Category | Modernization Pathway | Findings |
|---|---|---|---|
| 1 | Authentication Foundation | Machine Identity | N |

Source: `remediation_roadmap.items[]`

**Recommended Actions:**
- Custom Transformation row (always present)
- AWS Programs subsection: EBA, MAP

**Agent Deployment Recommendation** (footer block):

```
{emoji} {tier_label}

This repository has {n} blocker(s) that must be resolved before any agent deployment.
Focus on the High severity findings above.
```

**Footer:**
- `Generated by AWS Transform · Agentic Readiness Analysis Report`
- `© {year} Amazon Web Services, Inc. All rights reserved.`

#### Data Sourcing (JSON → HTML mapping)

| Visual location | JSON source |
|---|---|
| Header | `metadata.{portfolio_name, analysis_date, language, loc}` + `repo_name` |
| Overall Analysis | `classification.tier` + `classification.sub_qualifier` |
| Stats cards | `counts.{high, medium, low, total}` |
| Technology Stack | `metadata.tech_stack.*` |
| Findings by Dimension | Per-category counts from `findings[]` + `severity_status` |
| Detailed Findings | `findings[]` (all 12 fields) |
| Remediation Roadmap | `remediation_roadmap.items[]` |
| Recommended Actions | `recommended_actions[]` |
| Deployment Recommendation | `classification.tier` → emoji mapping |

**Content NOT in HTML** (MD-only): Rubric quotes, compensating-control discussion, BLOCKER Remediation blocks, conditional-resolution reasoning, DATA-Q1 sub-checks.

### Slug Derivation

The `{repo-name}` placeholder in artifact filenames refers to the **slug**, not the filesystem basename. The slug is derived as follows:

```
slug = lowercase(repo.name)
       with any character not in [a-z0-9_-] replaced by '-'
```

When this TD is invoked via the orchestrator, the slug source is the `name` field of the repository entry in `portfolio-config.yaml`. When invoked manually, the slug source is provided implicitly via the working directory's `additionalPlanContext` or, in absence, the repository's directory name normalized by the rule above. **Always derive from the configured name, not the on-disk basename** — they can mismatch (e.g., a `MonoToMicroLegacy` directory configured as `unishop-monolith`).

### Artifact Layout

```
{portfolio-or-repo}/
└── services/
    └── {repo-name}/
        └── agentic-readiness-analysis/
            ├── {repo-name}-ara-report.md
            ├── {repo-name}-ara-report.json
            ├── {repo-name}-ara-report.html
            └── {repo-name}-ara-report.metadata.json
```


---

## Error Handling

The TD is explicit about failure modes — no defensive inference, no silent skips. Failures name the offending element (question_id, file path, field) so assessors can remediate.

### Required-Field Failure

IF any of the 12 required per-finding fields is absent from an emitted finding, THEN the analysis SHALL fail, naming:
- The `question_id` of the offending finding
- The specific missing field

Example failure message: `"Analysis failed: finding for AUTH-Q1 is missing required field 'recommendation'. All 12 per-finding fields are REQUIRED."`

### N/A / Not Evaluated Leak

IF a finding is emitted for a question whose resolution was N/A or Not Evaluated, THEN the analysis SHALL fail, naming the `question_id` and the resolution status that should have been recorded in `evaluations[]` instead.

Example: `"Analysis failed: finding emitted for DATA-Q5 but the question resolved to N/A (no persistent data store). N/A / Not Evaluated resolutions MUST be recorded in evaluations[] only."`
