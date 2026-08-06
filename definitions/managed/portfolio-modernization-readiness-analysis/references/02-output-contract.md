# Portfolio MOD Output Contract

> **Purpose:** Loaded by the Portfolio Modernization Readiness Analysis (portfolio-mod) TD to emit its four-artifact bundle. Defines the JSON contract, top-level JSON keys, pathways aggregation, remediation roadmap, recommended actions, MD-retained execution-roadmap content, the HTML visual contract, and error handling. This is the machine-readable contract the webapp consumes.

---

---

## Output Contract

This section defines the portfolio MOD JSON contract, HTML visual contract, and error-handling behavior. The MD sections above remain the narrative artifact; the JSON is the canonical machine-readable contract consumed by the webapp; the HTML is a single self-contained visualization.

---

### Four-Artifact Output Contract (Portfolio MOD)

Every portfolio MOD analysis emits four artifacts: three report artifacts plus a metadata sidecar. All four files use the same base name derived from the portfolio name.

| Artifact | Filename | Purpose |
|---|---|---|
| Markdown report | `{portfolio-name}-portfolio-mod-report.md` | Narrative-prose artifact. Contains every section defined above (Executive Dashboard, Technology Stack, Dependency Map, Cross-Cutting Concerns, Roadmap, Pathways, Integration Opportunities, Risk Analysis, Resource Allocation, AWS Programs, Learning Materials, Service-by-Service Summary). |
| JSON report | `{portfolio-name}-portfolio-mod-report.json` | **Canonical machine-readable contract.** Consumed by the webapp dashboard. Every semantic field defined in the Top-Level JSON Keys section below MUST be present. |
| HTML report | `{portfolio-name}-portfolio-mod-report.html` | **Single self-contained HTML file** (no external asset fetches at render time). Renders a subset of the JSON per the Portfolio MOD HTML Visual Contract below. MUST be emitted alongside the MD and JSON — it is NOT optional. |
| Metadata sidecar | `{portfolio-name}-portfolio-mod-report.metadata.json` | Tiny JSON file carrying version compatibility data. |

The JSON artifact is the canonical contract. If any artifacts disagree on a field, JSON wins.

#### Artifact Layout

The four-artifact bundle is emitted at the **portfolio root** under the `modernization-readiness-analysis/` directory:

```
{portfolio-root}/
└── modernization-readiness-analysis/
    ├── {portfolio-name}-portfolio-mod-report.md
    ├── {portfolio-name}-portfolio-mod-report.json
    ├── {portfolio-name}-portfolio-mod-report.html
    └── {portfolio-name}-portfolio-mod-report.metadata.json
```

The directory `modernization-readiness-analysis/` is the same canonical location used for per-repo MOD reports (which live one level deeper, under `services/{repo-name}/modernization-readiness-analysis/`). Per-repo and portfolio reports are distinguished by the filename prefix: per-repo uses `{repo-name}`, portfolio uses `{portfolio-name}-portfolio`.

#### Metadata Sidecar Fields

```json
{
  "analysis_type": "portfolio-mod",
  "analysis_date": "YYYY-MM-DD",
  "td_version": "portfolio-modernization"
}
```

---

### Top-Level JSON Keys

The Portfolio MOD JSON artifact MUST emit these top-level keys in the order shown:

| Key | Description |
|---|---|
| `analysis_type` | Literal `"portfolio-mod"` |
| `metadata` | Version, analysis date, portfolio name, TD version, services_analyzed, consumed_per_repo_json_files, preferences (optional) |
| `summary` | 5 KPI counts: repositories_analyzed, total_findings, high_severity_findings, medium_severity_findings, low_severity_findings |
| `filter_vocab` | Filter-eligible enums actually present in the run |
| `executive_dashboard` | Portfolio score overview + `score_band_distribution` + `tier_distribution` (counts that agree) + category_score_averages + repo_type_distribution |
| `technology_stack_summary` | Technology stack section |
| `repositories[]` | Per-repo roll-up |
| `findings[]` | Lightweight portfolio finding index. See "Portfolio `findings[]` entry shape" below. |
| `remediation_roadmap` | See §"Remediation Roadmap" — grouping `pathway` |
| `recommended_actions[]` | Canonical AWS programs (MAP, MMP, WAMP, EBA, OLA, VMP, ISV WMP) |
| `pathways[]` | All 7 AWS Modernization Pathways with JSON-pointer back-references; see §"Pathways Aggregation" |
| `dependency_map` | Portfolio dependency map |
| `roadmap_phases[]` | Optional, additive |
| `parallel_execution_tracks[]` | Optional, additive |
| `portfolio_risk_register[]` | Optional, additive |

Canonical shape is fully defined by the Top-Level JSON Keys table above. All required keys, types, and nesting are specified inline in this TD.

#### `filter_vocab`

```json
{
  "severities": ["High", "Medium", "Low"],
  "categories": ["Infrastructure & DevOps", "Application Architecture", "Data Platform", "Security Baseline", "Operations & Observability"],
  "efforts": ["High", "Medium", "Low"],
  "priorities": ["P0", "P1", "P2", "P3"],
  "phases": [1, 2, 3, 4],
  "classifications": ["Cloud-Native Ready", "Pilot-Ready", "Remediation Required", "Not Ready"]
}
```

Display names only for categories.

#### `executive_dashboard` dual-distribution

`executive_dashboard` MUST carry both `score_band_distribution` (numeric-score bands) and `tier_distribution` (tier counts). The two must agree under the canonical equivalence table:
- Mature (≥3.5) ≡ Cloud-Native Ready
- Partial (2.5–3.4) ≡ Pilot-Ready
- Needs Work (1.5–2.4) ≡ Remediation Required
- Not Ready (<1.5) ≡ Not Ready

```json
"executive_dashboard": {
  "portfolio_score_overview": { "portfolio_overall_score": 2.31, "score_range": { "min": 1.22, "max": 3.75 } },
  "score_band_distribution": { "mature": 3, "partial": 8, "needs_work": 18, "not_ready": 5 },
  "tier_distribution": { "cloud_native_ready": 3, "pilot_ready": 8, "remediation_required": 18, "not_ready": 5 },
  "category_score_averages": [ { "category_id": "INF", "category": "Infrastructure & DevOps", "average": 1.45 } ],
  "repo_type_distribution": { "application": 16, "monorepo": 18 }
}
```

#### `repositories[]`

Each entry carries:
- `repo_name`
- `overall_score` (numeric 1.00-4.00)
- `classification.tier` + `classification.classification_consistency_check` ("consistent" OR a structured `{status: "divergent", score_band, count_tier, reason}` object)
- `category_scores[]` — each entry with `numeric_score` + `score_rating` + `severity_status`
- `surface_flags`, `repo_type`, `service_archetype`, `repository_priority`
- `per_repo_md_path`, `per_repo_json_path`, `per_repo_html_path`
- `pathways_triggered[]` — OBJECT list (not bare IDs) where each entry carries `{id, priority, effort, triggering_questions[]}` with inlined `(question_id, score, note, evidence)`.

#### Portfolio `findings[]` entry shape

Each entry is a **lightweight per-repo finding reference** (not a full copy). Rationale: the webapp Findings tab only needs enough to render a sortable, filterable table; full prose (`description`, `gap`, `recommendation`) is available in the per-repo JSON via click-through. Keeping the portfolio JSON lightweight prevents it from growing quadratically with portfolio size.

Each entry carries these 11 fields:

| Field | Type | Description |
|---|---|---|
| `question_id` | string | MOD rubric question identifier (e.g., `"INF-Q1"`). |
| `repo_name` | string | Source repository name (matches `repositories[].repo_name`). |
| `category` | string | Webapp-facing category display name (e.g., `"Infrastructure & DevOps"`). |
| `category_id` | string | Rubric short code (e.g., `"INF"`). |
| `title` | string | Short finding title from the per-repo report. |
| `severity` | enum | `"High"` / `"Medium"` / `"Low"` — unified severity. |
| `priority` | enum | `"P0"` / `"P1"` / `"P2"` / `"P3"` — per-question priority (static). |
| `effort` | enum | `"High"` / `"Medium"` / `"Low"` — remediation effort estimate. |
| `phase` | integer | `1`–`4` — derived roadmap phase. |
| `evidence` | object or null | `{file, lines}` reference or `null`. |
| `mod_metadata` | object | `{internal_score, score_label, archetype_calibrated, core_question}` — per-finding metadata. |

**Fields NOT present in the portfolio `findings[]` entry** (by design — available via per-repo JSON click-through):
- `description`, `gap`, `recommendation` — these are full-prose fields in the per-repo MOD JSON. The portfolio aggregates but does not duplicate them. The webapp Findings tab uses `title` + severity + priority + evidence for its row summary, and links to the per-repo JSON for full detail.

Findings are sourced by reading each consumed per-repo MOD JSON's `findings[]` and projecting the 11 fields above plus `repo_name`. Ordering: severity descending (High → Medium → Low), then repo_name, then category display order (INF → APP → DATA → SEC → OPS).

Findings are NEVER emitted for questions that resolve to passing (score 4), N/A, Not Evaluated (archetype-N/A), or Not Evaluated (surface-gated) at the per-repo level — the portfolio `findings[]` array only contains rows for which the source per-repo MOD JSON emitted a finding.

---

### Pathways Aggregation

`pathways[]` aggregates per-repo pathway information across all consumed repos. Every entry carries:

```json
{
  "id": "move-to-cloud-native",
  "name": "Move to Cloud Native",
  "portfolio_status": "Triggered",
  "triggered_in_repos_count": 18,
  "applicable_repos_count": 32,
  "priority": "High",
  "effort": "High",
  "description": "Decompose monoliths, adopt serverless patterns, implement event-driven architecture.",
  "recommended_aws_programs": ["Migration Acceleration Program (MAP)", "EBA"],
  "contributing_repos": [
    {
      "repo_name": "Lidarr--Lidarr",
      "per_repo_pathway_source": "/pathways/0",
      "per_repo_json_path": "services/Lidarr--Lidarr/modernization-readiness-analysis/Lidarr--Lidarr-mod-report.json",
      "triggering_questions": [
        { "question_id": "APP-Q2", "score": 2, "note": "Monolith", "evidence": { "file": "src/", "lines": null } },
        { "question_id": "INF-Q1", "score": 1, "note": "No managed compute", "evidence": { "file": "azure-pipelines.yml", "lines": null } }
      ]
    }
  ],
  "per_repo_not_triggered_reasons": [
    { "repo_name": "arrow-py--arrow", "consulted_questions": [ { "question_id": "APP-Q2", "score": 4, "note": "Primary trigger not met." } ] }
  ],
  "roadmap_phase_alignment": "Phase 2-3"
}
```

#### JSON-pointer back-reference

`contributing_repos[].per_repo_pathway_source` MUST be a JSON-pointer fragment (RFC 6901) of the form `/pathways/{index}` where `{index}` names the exact position in the per-repo MOD JSON's `pathways[]` array. ALTERNATIVELY, a URI reference form ending in `#/pathways/{index}` is accepted. The portfolio TD MUST NOT emit a best-effort match by name or id — the JSON-pointer is authoritative. Unresolvable pointers fail the analysis (see error-handling section below).

#### Inlined evidence

`triggering_questions[].evidence` is INLINED on the portfolio entry (copied from per-repo `findings[].evidence` for the triggering question id) so the webapp can render pathway evidence in the Pathways tab without a second per-repo JSON fetch.

---

### Remediation Roadmap

The Portfolio MOD JSON emits `remediation_roadmap` with `grouping: "pathway"`:

```json
"remediation_roadmap": {
  "grouping": "pathway",
  "total_pathways": 4,
  "total_items": 4,
  "items": [
    {
      "pathway_id": "move-to-cloud-native",
      "pathway": "Move to Cloud Native",
      "description": "…",
      "repos_count": 18,
      "applicable_repos_count": 32,
      "priority": "High",
      "effort": "High"
    }
  ]
}
```

`items[]` is a ONE-TO-ONE summary projection of `pathways[]` entries with `portfolio_status == "Triggered"`, sorted descending by `triggered_in_repos_count`. Consumers needing per-repo evidence dereference through `pathways[].contributing_repos[]`.

MD rendering under an H2 heading **"## Remediation Roadmap"** matching the webapp tab label.

---

### Recommended Actions

The Portfolio MOD JSON emits `recommended_actions[]` with minimum-set coverage:

| `id` | `name` | `acronym` | `type` |
|---|---|---|---|
| `map` | Migration Acceleration Program | MAP | program |
| `mmp` | Microsoft Modernization Program | MMP | program |
| `wamp` | Windows App Modernization Program | WAMP | program |
| `eba` | Experience-Based Acceleration | EBA | program |
| `ola` | Optimization and Licensing Analysis | OLA | program |
| `vmp` | VMware Migration Program | VMP | program |
| `isv-wmp` | ISV Workload Migration Program | ISV WMP | program |

Same entry envelope as Portfolio ARA. `status ∈ {Triggered, Applicable, Not Triggered}` with non-empty `trigger_reason`. Emitted under the H2 heading **"## Recommended Actions"**.

---

### MD-Retained Execution-Roadmap Content

The Portfolio MOD MD artifact contains the following sections:

- Sequencing Principles (numbered list)
- Phase 0 Cross-Cutting Foundation
- Phase 1 Quick Wins
- Phase 2 Foundation
- Phase 3 Advanced
- Total Portfolio Effort
- Per-service modernization plans with per-service Dependencies and Estimated Effort
- Parallel Execution Tracks
- Pathway Details subsections with Cross-Service Synergies / Roadmap Phase Alignment / Relevant Learning Materials per triggered pathway
- Integration Opportunities
- Risk Analysis (Portfolio Risk Register table)
- Resource Allocation Recommendations
- Recommended Self-Paced Learning Materials

The JSON `remediation_roadmap.items[]` is a summary projection of these MD sections.

#### Additive structured JSON fields

Four execution-roadmap fields are also emitted as additive structured JSON alongside the MD content:

1. **Top-level `roadmap_phases[]`**:
   ```json
   [{ "phase": 0, "name": "Cross-Cutting Foundation", "calendar_window": "Months 0-3", "objective": "…", "estimated_effort": "Medium" }]
   ```

2. **`pathways[].roadmap_phase_alignment`**: optional string per pathway (e.g., `"Phase 2-3"`) aligning the pathway with the roadmap phases.

3. **Top-level `parallel_execution_tracks[]`**:
   ```json
   [{ "track_name": "Database Track", "pathways": ["move-to-managed-databases"], "repos_count": 14, "can_run_in_parallel": true, "dependencies": [] }]
   ```

4. **Top-level `portfolio_risk_register[]`**:
   ```json
   [{ "risk": "Lift-and-shift stalls modernization ROI", "likelihood": "Medium", "impact": "High", "priority": "P1", "mitigation": "Pair lift-and-shift with Move to Containers milestones", "phase": 2 }]
   ```

These additive JSON fields are optional and exist so consumers can reason about the roadmap structurally without parsing MD.

---

### Portfolio MOD HTML Visual Contract

The portfolio MOD HTML artifact is a single self-contained file rendering a subset of the portfolio JSON. The full visual contract is inlined below — do NOT reference external files.

#### HTML Structure and Layout

**Header:**
- Title: `Modernization Readiness - {portfolio_name}`
- Subtitle line: `{date} · {N} repositories`

**Executive Summary** (top section, above the tab bar):

Prose intro: "This Modernization Readiness Analysis evaluates whether your {N} repositories are prepared for cloud-native transformation. The analysis examines five key dimensions: Infrastructure & DevOps, Application Architecture, Data Platform, Security Baseline, and Operations & Observability."

Subsections:
1. **Portfolio Status** — "Out of {N} repositories analyzed, {A} are cloud-native ready..., {B} are pilot-ready..., and {C} require remediation... The analysis identified {H} high severity findings (blockers) and {M} medium severity findings (risks)."
2. **Key Findings** — Top 5 cross-cutting high severity areas as bullet list with repo counts
3. **Remediation Plan** — 3-phase roll-up with finding counts and timelines
4. **Recommended Actions** — Bullet list of triggered AWS programs with reasons

**Stats Card Row** (4 cards):

| Card | Value source | Subtitle |
|---|---|---|
| Total Findings | `summary.total_findings` | Across all {M} repositories |
| High Severity | `summary.high_severity_findings` | Critical findings |
| Medium Severity | `summary.medium_severity_findings` | Important findings |
| Low Severity | `summary.low_severity_findings` | Minor findings |

**Charts Row** (2 visualizations):
- **Portfolio Distribution** — pie/donut chart from `executive_dashboard.tier_distribution`
- **Severity by Repository** — stacked bar chart from per-repo `counts.{high, medium, low}` in `repositories[]`

(MOD portfolio does NOT have a Section Heatmap — that's ARA-only.)

**Tab bar order:** Repositories → Findings → Remediation → Pathways

#### Repositories Tab

Table columns: `Name`, `Language`, `LOC`, `Total`, `High`, `Medium`, `Low`, `Readiness`

- Source: `repositories[]`
- Readiness = `classification.tier`
- Ordered by High count descending, then alphabetical
- MOD includes the `Low` column (ARA omits it)

#### Findings Tab

Download CSV control in header.

Table columns: `Category`, `Repository`, `Finding Description`, `Remediation`, `Severity`, `Effort`

- Source: `findings[]`
- Finding Description = title (bold) + one-liner description
- Ordered by severity (High first), then repo name, then category

#### Remediation Roadmap Tab

4-phase table:

| Phase | Focus Area | Findings | Timeline | Key Actions |
|---|---|---|---|---|
| Phase 1 | Infrastructure Foundation | N | 4-6 weeks | IaC Adoption, Container Platform, CI/CD Pipelines |
| Phase 2 | Security & Data Platform | N | 3-4 weeks | Secrets Management, Database Migration, IAM Hardening |
| Phase 3 | Application Architecture | N | 4-8 weeks | API Modernization, Service Decomposition, Event-Driven |
| Phase 4 | Operations & Observability | N | 2-3 weeks | Distributed Tracing, Structured Logging, SLOs & Alerting |

Source: `remediation_roadmap.items[]` grouped by phase + `roadmap_phases[]`

#### AWS Programs & Engagement Recommendations

Table columns: `Program`, `Relevance`, `What You Get`, `Suggested Timing`

- Source: `recommended_actions[]`
- Relevance values: `Triggered`, `Applicable`, `Not Triggered`
- Show ALL programs (not just triggered)

#### Pathways Tab (MOD-only — ARA does not have this)

Renders `pathways[]` with:
- `portfolio_status` (Triggered / Not Triggered / Not Applicable)
- `triggered_in_repos_count`
- `contributing_repos[].triggering_questions[]` evidence inlined

#### Footer

- `Generated by AWS Transform · Portfolio Modernization Readiness Analysis Report`
- `© {year} Amazon Web Services, Inc. All rights reserved.`

#### Data Sourcing (JSON → HTML mapping)

| Visual location | JSON source |
|---|---|
| Header | `metadata.{portfolio_name, analysis_date, services_analyzed}` |
| Executive Summary | `executive_dashboard.tier_distribution` + `summary.*` |
| Stats cards | `summary.{total_findings, high_severity_findings, medium_severity_findings, low_severity_findings}` |
| Portfolio Distribution chart | `executive_dashboard.tier_distribution` |
| Severity by Repository chart | Per-repo counts from `repositories[]` |
| Repositories table | `repositories[]` |
| Findings table | `findings[]` |
| Remediation Roadmap | `remediation_roadmap.items[]` grouped by phase |
| AWS Programs table | `recommended_actions[]` |
| Pathways tab | `pathways[]` |

**Content NOT in HTML** (MD-only): Sequencing Principles, per-service modernization steps, Parallel Execution Tracks, Cross-Service Synergies, Learning Materials, Portfolio Risk Register, Scoring Notes arithmetic.

**HTML-escaping discipline** applies to every attacker-controlled string.

---

## Error Handling

The portfolio TD consumes ONLY per-repo JSON. Failure modes are explicit, loud, and actionable.

### Missing Per-Repo JSON

IF any per-repo JSON listed in the portfolio configuration is missing from the consumed corpus, THEN the portfolio analysis SHALL fail with a message listing ALL missing files at once (not one at a time).

Example: `"Portfolio analysis failed: 3 per-repo JSON artifacts missing: services/foo--bar/modernization-readiness-analysis/foo--bar-mod-report.json, services/baz--qux/modernization-readiness-analysis/baz--qux-mod-report.json, services/wat--wub/modernization-readiness-analysis/wat--wub-mod-report.json."`

### Dangling Cross-Reference

IF a `question_id` or `repo_name` referenced in portfolio JSON does not resolve into at least one consumed per-repo JSON of the matching `analysis_type`, THEN the portfolio analysis SHALL fail naming the dangling reference.

Example: `"Portfolio analysis failed: findings[3].question_id='INF-Q99' does not match any rubric question in consumed MOD per-repo JSONs."`

### Unresolvable JSON-Pointer

IF a `pathways[].contributing_repos[].per_repo_pathway_source` JSON-pointer does NOT resolve to a valid index in the target per-repo MOD JSON's `pathways[]` array, THEN the portfolio analysis SHALL fail naming the pointer and the source file.

Example: `"Portfolio MOD analysis failed: pathways[1].contributing_repos[2].per_repo_pathway_source='/pathways/9' exceeds the per-repo pathways[] cardinality (7) in services/Lidarr--Lidarr/modernization-readiness-analysis/Lidarr--Lidarr-mod-report.json."`

### No Silent Fallback

The portfolio TD SHALL NOT fall back to parsing per-repo MD or HTML. If per-repo JSON is unavailable, unreadable, or invalid, the analysis fails. The portfolio TD consumes JSON-only.
