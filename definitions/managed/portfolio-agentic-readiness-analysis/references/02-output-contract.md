# Portfolio ARA Output Contract

> **Purpose:** Loaded by the Portfolio Agentic Readiness Analysis (portfolio-ara) TD to emit its four-artifact bundle. Defines the four-artifact contract, top-level JSON keys, remediation roadmap, recommended actions, the HTML visual contract, and error handling. This is the machine-readable contract the webapp consumes.

---

---

### Four-Artifact Output Contract (Portfolio ARA)

Every portfolio ARA analysis emits four artifacts: three report artifacts plus a metadata sidecar. All four files use the same base name derived from the portfolio name.

| Artifact | Filename | Purpose |
|---|---|---|
| Markdown report | `{portfolio-name}-portfolio-ara-report.md` | Richest-prose artifact. Contains Executive Dashboard, Cross-Cutting Analysis, Dependency Map, Agentic Program Recommendations, Readiness Profiles, and Service-by-Service Summary. |
| JSON report | `{portfolio-name}-portfolio-ara-report.json` | **Canonical machine-readable contract.** Consumed by the webapp dashboard. Every semantic field defined in the Top-Level JSON Keys section below MUST be present. |
| HTML report | `{portfolio-name}-portfolio-ara-report.html` | **Single self-contained HTML file** (no external asset fetches at render time). Renders a subset of the JSON per the Portfolio ARA HTML Visual Contract below. MUST be emitted alongside the MD and JSON — it is NOT optional. |
| Metadata sidecar | `{portfolio-name}-portfolio-ara-report.metadata.json` | Tiny JSON file carrying version compatibility data. |

The JSON artifact is the canonical contract. If any artifacts disagree on a field, JSON wins.

#### Artifact Layout

The four-artifact bundle is emitted at the **portfolio root** under the `agentic-readiness-analysis/` directory:

```
{portfolio-root}/
└── agentic-readiness-analysis/
    ├── {portfolio-name}-portfolio-ara-report.md
    ├── {portfolio-name}-portfolio-ara-report.json
    ├── {portfolio-name}-portfolio-ara-report.html
    └── {portfolio-name}-portfolio-ara-report.metadata.json
```

The directory `agentic-readiness-analysis/` is the same canonical location used for per-repo ARA reports (which live one level deeper, under `services/{repo-name}/agentic-readiness-analysis/`). Per-repo and portfolio reports are distinguished by the filename prefix: per-repo uses `{repo-name}`, portfolio uses `{portfolio-name}-portfolio`.

#### Metadata Sidecar Fields

```json
{
  "analysis_type": "portfolio-ara",
  "analysis_date": "YYYY-MM-DD",
  "td_version": "portfolio-agentic-readiness"
}
```

---

### Top-Level JSON Keys

The Portfolio ARA JSON artifact MUST emit these top-level keys in the order shown:

| Key | Description |
|---|---|
| `analysis_type` | Literal `"portfolio-ara"` |
| `metadata` | Version, analysis date, portfolio name, TD version, services_analyzed, consumed_per_repo_json_files count |
| `summary` | 5 KPI counts: repositories_analyzed, total_findings, high_severity_findings, medium_severity_findings, low_severity_findings |
| `filter_vocab` | Filter-eligible values for webapp UI chips |
| `executive_dashboard` | Readiness distribution, portfolio summary, repo-type distribution, blocker heatmap |
| `repositories[]` | Per-repo roll-up |
| `findings[]` | Per-repo findings propagated up. Each entry is a 12-field per-repo finding plus `repo_name`. One entry per (repo × question_id). Used by webapp Findings tab. |
| `cross_cutting_findings[]` | Portfolio-aggregated findings where the same question_id fires at the same tier across 2+ repos (BLOCKER) or meets the scaling threshold (RISK, max(3, 33% of applicable repos)). One entry per question_id. Used by webapp Cross-Cutting view. |
| `remediation_roadmap` | See §"Remediation Roadmap" below |
| `recommended_actions[]` | Canonical agentic programs (AI DLC, AXE, Innovation EBA) |
| `portfolio_level_findings[]` | PORT-ARA-Q* cross-portfolio findings |
| `dependency_map` | Dependency map |

Canonical shape is fully defined by the Top-Level JSON Keys table above. All required keys, types, and nesting are specified inline in this TD.

#### `filter_vocab`

Contains ONLY values actually present in the run, so the webapp renders filter chips without extra network calls:

```json
{
  "severities": ["High", "Medium", "Low"],
  "categories": ["API Surface", "Authentication & Authorization", "State Management", "Human-in-the-Loop", "Data Accessibility", "Discovery & Documentation", "Observability", "Engineering Maturity"],
  "efforts": ["High", "Medium", "Low"],
  "priorities": ["P0", "P1", "P2", "P3"],
  "phases": [1, 2, 3],
  "classifications": ["Agent-Ready", "Pilot-Ready", "Pilot-Ready (Safety Concerns)", "Remediation Required", "Not Agent-Integrable"],
  "safety_impact": [true, false],
  "native_severities": ["BLOCKER", "RISK-SAFETY", "RISK-QUALITY", "INFO"]
}
```

`filter_vocab.categories[]` carries display names only — NOT short codes.

#### `findings[]` vs `cross_cutting_findings[]` — two distinct arrays

The Portfolio ARA JSON emits **two separate finding arrays**, each with its own schema and purpose:

1. **`findings[]`** — per-repo findings propagated up from the consumed per-repo ARA JSONs. One entry per (repo × question_id) with a `repo_name` field so the webapp can filter by repo. Each entry uses the same 12-field shape as per-repo findings plus `repo_name`. Used by the webapp's Findings tab.

2. **`cross_cutting_findings[]`** — portfolio-aggregated findings where the same question_id appears as BLOCKER in 2+ repos or RISK meeting the scaling threshold (max(3, 33% of applicable repos); see Step 4 and Step 4b). One entry per question_id with aggregated metadata (`affected_repos_count`, `applicable_repos_count`, `affected_services[]`, `cross_cutting_type`). Used by the webapp's Cross-Cutting Concerns view.

Both arrays coexist — `findings[]` answers "what's wrong per-repo?" and `cross_cutting_findings[]` answers "what's wrong across the portfolio?". A single question_id may appear in both arrays: once per repo in `findings[]`, and once aggregated in `cross_cutting_findings[]`.

#### `findings[]` entry shape (per-repo propagation)

Each entry mirrors the per-repo ARA 12-field finding shape, plus `repo_name`:

| Field | Type | Description |
|---|---|---|
| `question_id` | string | Rubric question identifier (e.g., `"AUTH-Q1"`). |
| `repo_name` | string | Source repository name (matches `repositories[].repo_name`). |
| `category` | string | Webapp-facing category display name (e.g., `"Authentication & Authorization"`). |
| `category_id` | string | Rubric short code (e.g., `"AUTH"`). |
| `title` | string | Short finding title. |
| `description` | string | Finding description. |
| `gap` | string | What's missing or incorrect. |
| `recommendation` | string | Remediation recommendation. |
| `severity` | enum | `"High"` / `"Medium"` / `"Low"` — unified severity. |
| `native_severity` | enum | `"BLOCKER"` / `"RISK-SAFETY"` / `"RISK-QUALITY"` / `"INFO"` — ARA native severity for portfolio grouping. |
| `safety_impact` | boolean | `true` for RISK-SAFETY findings and BLOCKERs flagged as agent-safety hazards. |
| `priority` | enum | `"P0"` / `"P1"` / `"P2"` / `"P3"` — per-question priority (static per question_id). |
| `effort` | enum | `"High"` / `"Medium"` / `"Low"` — remediation effort estimate. |
| `phase` | integer | `1`–`3` — derived roadmap phase (Phase 1 = blockers, Phase 2 = safety, Phase 3 = quality). |
| `evidence` | object or null | `{file, lines}` reference or `null`. |

Findings are sourced from each consumed per-repo ARA JSON's `findings[]` array; the portfolio TD adds `repo_name` and emits them into a flat array. Ordering: severity descending, then repo_name, then category display order (API → AUTH → STATE → HITL → DATA → DISC → OBS → ENG).

Findings are NEVER emitted for questions that resolve to pass, N/A, or Not Evaluated at the per-repo level — the portfolio `findings[]` array only contains rows for which the source per-repo ARA JSON emitted a finding.

#### `cross_cutting_findings[]` entry shape (portfolio aggregation)

Each entry aggregates the same question_id across multiple repos where it fires at the same tier:

| Field | Type | Description |
|---|---|---|
| `question_id` | string | Rubric question identifier. |
| `category` | string | Webapp-facing category display name. |
| `category_id` | string | Rubric short code. |
| `title` | string | Short finding title (shared across affected repos). |
| `severity` | enum | `"High"` / `"Medium"` / `"Low"` — unified severity of the aggregated tier. |
| `native_severity` | enum | `"BLOCKER"` / `"RISK-SAFETY"` / `"RISK-QUALITY"` / `"INFO"` — native severity. |
| `cross_cutting_type` | enum | `"blocker"` / `"risk_safety"` / `"risk_quality"` — the tier that triggered this cross-cutting entry. |
| `affected_repos_count` | integer | Number of repos where this question fires at this tier. |
| `applicable_repos_count` | integer | Number of repos where this question is not N/A (denominator). |
| `affected_services` | string[] | Repo names where this question fires at this tier. |
| `common_finding_summary` | string | Prose summary of the finding pattern across affected repos. |
| `root_cause_pattern` | string | Common root cause identified across repos. |
| `portfolio_remediation` | object | `{approach, immediate_action, target_state, estimated_effort, priority, dependencies[]}` per Step 6.1. |

Cross-cutting entries are generated per Step 4 (BLOCKER threshold: 2+ repos OR fan-in escalation) and Step 4b (RISK threshold: max(3, 33% of applicable repos)). Step 6 populates `portfolio_remediation` for each entry.

---

### Remediation Roadmap

The Portfolio ARA JSON emits `remediation_roadmap` with `grouping: "phase_category"`. Each `items[]` entry carries:

```json
{
  "phase": 1,
  "category": "Machine Identity Authentication",
  "category_question_id": "AUTH-Q1",
  "native_severity": "BLOCKER",
  "severity": "High",
  "safety_impact": true,
  "common_finding_summary": "…",
  "root_cause_pattern": "…",
  "remediation": "Implement OAuth2 client credentials or per-agent API keys with principal attribution",
  "remediation_detail": {
    "approach": "per_service_fix",
    "immediate_action": "…",
    "target_state": "…",
    "dependencies": []
  },
  "affected_repos_count": 11,
  "applicable_repos_count": 34,
  "effort": "Medium",
  "priority": "P0",
  "affected_services": [
    {
      "repo_name": "Lidarr--Lidarr",
      "per_repo_evidence": { "file": "src/…/HostConfigResource.cs", "lines": "10-45" },
      "agent_scope": "read-only",
      "resolution_reasoning": "…",
      "conditional_resolution": "…"
    }
  ],
  "also_affected_at_lower_severity": [
    { "repo_name": "FlowiseAI--Flowise", "resolved_severity": "RISK-SAFETY", "reason": "B2 — framework-hook defaults" }
  ]
}
```

#### Sources for item fields (JSON-only consumption)

- `per_repo_evidence` sourced from per-repo ARA JSON `findings[].evidence`. NEVER parsed from per-repo MD.
- `conditional_resolution` and `agent_scope` sourced from per-repo ARA JSON `findings[].ara_metadata.{conditional_resolution, agent_scope}` for the five conditional BLOCKERs (API-Q4, STATE-Q1, AUTH-Q6, DATA-Q1, DATA-Q2).
- `also_affected_at_lower_severity[]` populated for DATA-Q1 items when different repos' B1/B2/B3 sub-checks fire at different severity tiers. Sourced from per-repo `findings[].ara_metadata.data_q1_subchecks`.

#### MD rendering

The Portfolio ARA MD artifact renders these items under an H2 heading **"## Remediation Roadmap"** that matches the webapp tab label. Each item is rendered as an H3 subsection with:
- Title: `"Phase {N} — {category}"`
- Table of `{affected_services, per_repo_evidence, agent_scope, resolution_reasoning}`
- Cross-Cutting narratives (BLOCKER Remediation blocks, Cross-Cutting RISK-SAFETY prose, Cross-Cutting RISK-QUALITY prose) are retained verbatim within the item.

The ARA execution-sequencing narrative (Phase 1 BLOCKER resolution, Phase 2 RISK-SAFETY hardening, Phase 3 RISK-QUALITY improvements) is preserved in MD prose.

---

### Recommended Actions

The Portfolio ARA JSON emits `recommended_actions[]` as an array of agentic-program entries. Minimum-set coverage:

| `id` | `name` | `acronym` | `type` |
|---|---|---|---|
| `ai-dlc` | AI Driven Development Lifecycle | AI DLC | workshop |
| `axe` | Agent Experience Engagement | AXE | program |
| `innovation-eba` | Innovation EBA | Innovation EBA | program |

Each entry carries:

```json
{
  "id": "axe",
  "name": "Agent Experience Engagement",
  "acronym": "AXE",
  "type": "program",
  "status": "Triggered",
  "trigger_reason": "19 BLOCKERs across authentication and data classification; structured implementation engagement recommended.",
  "suggested_timing": "After initial triage",
  "duration": "4-week engagement",
  "what_it_provides": "Hands-on agent-integration engagement with AWS Solutions Architects."
}
```

`status` ∈ {Triggered, Applicable, Not Triggered}. `trigger_reason` is non-empty prose explaining why the program fires.

The MD artifact renders this under an H2 heading **"## Recommended Actions"**. The "## Agentic Program Recommendations" label is retained as an H3 subheading under that H2 to preserve rich program prose without creating duplicate H2s.

---

### Portfolio ARA HTML Visual Contract

The portfolio ARA HTML artifact is a single self-contained file rendering a subset of the portfolio JSON. The full visual contract is inlined below — do NOT reference external files.

#### HTML Structure and Layout

**Header:**
- Title: `Agentic Readiness - {portfolio_name}`
- Subtitle line: `{date} · {N} repositories · agent_scope: {agent_scope}`

**Executive Summary** (top section, above the tab bar):

Prose intro: "This Agentic Readiness Analysis evaluates whether your {N} repositories can safely integrate with autonomous AI agents. The analysis examines eight key dimensions (API Surface, Authentication & Authorization, State Management, Human-in-the-Loop, Data Accessibility, Discovery & Documentation, Observability, Engineering Maturity)..."

Subsections:
1. **Portfolio Status** — "Out of {N} repositories analyzed, {A} are agent-ready and can integrate with AI agents immediately, {B} are pilot-ready for read-only operations, and {C} require remediation before agent deployment. The analysis identified {H} high severity findings (blockers) and {M} medium severity findings (risks)."
2. **Key Findings** — Top 3 cross-cutting high severity areas as bullet list with repo counts
3. **Remediation Plan** — 3-phase numbered list with finding counts and timelines
4. **Recommended Actions** — Bullet list of triggered programs (AI DLC, AXE, Innovation EBA) with reasons

**Stats Card Row** (4 cards):

| Card | Value source | Subtitle |
|---|---|---|
| Total Findings | `summary.total_findings` | Across {M} repositories |
| High Severity | `summary.high_severity_findings` | Blockers that must be fixed |
| Medium Severity | `summary.medium_severity_findings` | Safety and quality risks |
| Agent-Ready | `executive_dashboard.readiness_distribution.agent_ready.count` | Ready for integration |

(ARA swaps "Low Severity" for "Agent-Ready" — this is ARA-specific.)

**Charts Row** (3 visualizations):
- **Portfolio Distribution** — pie/donut chart from `executive_dashboard.readiness_distribution`
- **Severity by Repository** — stacked bar chart from per-repo counts in `repositories[]`
- **Section Heatmap** — grid heatmap from `executive_dashboard.blocker_heatmap_by_section[]` (ARA-only)

**Tab bar order:** Repositories → Findings → Remediation → AWS Programs. NO Pathways tab — pathways are MOD-only.

#### Repositories Tab

Table columns: `Name`, `Language`, `LOC`, `Total Findings`, `High Severity`, `Medium Severity`, `Agentic Readiness`

- Source: `repositories[]`
- Agentic Readiness = `classification.tier` (potentially with `sub_qualifier`)
- Ordered by High count descending, then alphabetical
- ARA **omits** the `Low Severity` column (MOD includes it)

#### Findings Tab

Download CSV control in header.

Table columns: `Category`, `Repository`, `Finding Description`, `Remediation`, `Severity`, `Effort`

- Source: `findings[]`
- Finding Description = title (bold) + one-liner description
- Ordered by severity (High first), then repo name, then category

#### Remediation Roadmap Tab

3-phase table:

| Phase | Focus Area | Findings | Timeline | Key Actions |
|---|---|---|---|---|
| Phase 1 | Blockers — Must Fix Before Agent Deployment | N | 3-6 weeks | Machine Identity Auth, Data Classification, API Documentation |
| Phase 2 | Safety Risks — Required for Production | N | 2-4 weeks | Audit Logging, Rollback, Rate Limiting, Authorization |
| Phase 3 | Quality Risks — Recommended for Operations | N | 2-4 weeks | Distributed Tracing, Schema Versioning, Error Handling, API Testing |

Source: `remediation_roadmap.items[]` grouped by phase

#### Recommended AWS Programs Tab

Table columns: `Program`, `Description`, `Why Recommended`, `Duration`

- Source: `recommended_actions[]` filtered to `status == "Triggered"`
- Canonical programs: AI DLC, AXE, Innovation EBA

#### Footer

- `Generated by AWS Transform · Portfolio Agentic Readiness Analysis Report`
- `© {year} Amazon Web Services, Inc. All rights reserved.`

#### Data Sourcing (JSON → HTML mapping)

| Visual location | JSON source |
|---|---|
| Header | `metadata.{portfolio_name, analysis_date, services_analyzed}` + agent_scope |
| Executive Summary | `summary.*` + `executive_dashboard.*` + `recommended_actions[]` |
| Stats cards | `summary.*` + `executive_dashboard.readiness_distribution.agent_ready.count` |
| Portfolio Distribution chart | `executive_dashboard.readiness_distribution` |
| Severity by Repository chart | Per-repo counts from `repositories[]` |
| Section Heatmap chart | `executive_dashboard.blocker_heatmap_by_section[]` |
| Repositories table | `repositories[]` |
| Findings table | `findings[]` |
| Remediation Roadmap | `remediation_roadmap.items[]` grouped by phase |
| AWS Programs table | `recommended_actions[]` |

**Content NOT in HTML** (MD-only): Sequencing Principles, per-service steps, Parallel Execution Tracks, Portfolio Risk Register, DATA-Q1 sub-check reasoning, conditional-resolution reasoning, root cause patterns.

**HTML-escaping discipline** applies to every attacker-controlled string (repo names, evidence file paths, finding titles, finding descriptions, prose fields).

---

## Error Handling

The portfolio TD consumes ONLY per-repo JSON. Failure modes are explicit, loud, and actionable.

### Missing Per-Repo JSON

IF any per-repo JSON listed in the portfolio configuration is missing from the consumed corpus, THEN the portfolio analysis SHALL fail with a message listing ALL missing files at once (not one at a time).

Example: `"Portfolio analysis failed: 3 per-repo JSON artifacts missing: services/foo--bar/agentic-readiness-analysis/foo--bar-ara-report.json, services/baz--qux/agentic-readiness-analysis/baz--qux-ara-report.json, services/wat--wub/agentic-readiness-analysis/wat--wub-ara-report.json."`

### Dangling Cross-Reference

IF a `question_id` or `repo_name` referenced in portfolio JSON does not resolve into at least one consumed per-repo JSON of the matching `analysis_type`, THEN the portfolio analysis SHALL fail naming the dangling reference.

Example: `"Portfolio analysis failed: findings[3].question_id='AUTH-Q9' does not match any rubric question in consumed ARA per-repo JSONs."`

### No Silent Fallback

The portfolio TD SHALL NOT fall back to parsing per-repo MD or HTML. If per-repo JSON is unavailable, unreadable, or invalid, the analysis fails. The TD consumes JSON-only.
