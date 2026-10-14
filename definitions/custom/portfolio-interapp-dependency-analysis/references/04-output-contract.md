# Output Contract

> **Purpose:** Loaded by the Portfolio Inter-Application Dependency (IAD) TD at Step 9. Defines the
> four-artifact bundle, the canonical JSON contract, the HTML visual contract, and error handling.

---

## Four-Artifact Output Contract

Every IAD run emits **four** artifacts sharing one base name. All four are mandatory; none is
optional, and a run that produces fewer than four has failed even if the Markdown looks complete.

| Artifact | Filename | Purpose |
|---|---|---|
| Markdown | `{portfolio-name}-portfolio-interapp-dep-report.md` | Narrative artifact. Sections per `references/03-report-template.md`. |
| JSON | `{portfolio-name}-portfolio-interapp-dep-report.json` | **Canonical machine-readable contract.** Every key below MUST be present. |
| HTML | `{portfolio-name}-portfolio-interapp-dep-report.html` | **Single self-contained file** — no external asset fetches at render time. MUST be emitted alongside MD and JSON. |
| Metadata sidecar | `{portfolio-name}-portfolio-interapp-dep-report.metadata.json` | Version and provenance compatibility data. |

The JSON is canonical. Where artifacts disagree on a field, JSON wins.

### Artifact layout

```
{portfolio-root}/
└── interapp-dependency-analysis/
    ├── {portfolio-name}-portfolio-interapp-dep-report.md
    ├── {portfolio-name}-portfolio-interapp-dep-report.json
    ├── {portfolio-name}-portfolio-interapp-dep-report.html
    └── {portfolio-name}-portfolio-interapp-dep-report.metadata.json
```

`interapp-dependency-analysis/` sits at the portfolio root, parallel to
`modernization-readiness-analysis/`. Writing into the MOD directory is prohibited — it would place
IAD output where MOD tooling globs for its own reports.

### Metadata sidecar

```json
{
  "analysis_type": "portfolio-interapp-dep",
  "analysis_date": "YYYY-MM-DD",
  "td_version": "portfolio-interapp-dependency-1.0.0",
  "portfolio_name_source": "supplied | derived_from_portfolio_mod | derived_from_workdir | default",
  "source_analysis_type": "modernization-readiness",
  "reports_consumed": 0,
  "reports_excluded": 0,
  "md_enrichment_available": 0
}
```

---

## Top-Level JSON Keys

Emit in this order. Every key is required; emit an empty array or object rather than omitting one.

| Key | Type | Description |
|---|---|---|
| `analysis_type` | string | Literal `"portfolio-interapp-dep"` |
| `metadata` | object | Portfolio name, date, TD version, counts, derived prefixes, context echo |
| `summary` | object | Headline KPI counts (see below) |
| `filter_vocab` | object | Enums actually present in this run |
| `nodes[]` | object[] | Every node: internal services, external systems, resources |
| `edges[]` | object[] | Every observed edge |
| `derived_edges[]` | object[] | Shared-resource-implied service pairs, kept separate from `edges[]` |
| `shared_resource_clusters[]` | object[] | Resource clusters with membership and coordination risk |
| `graph_metrics` | object | Per-node metrics plus portfolio-level graph statistics |
| `circular_dependencies` | object | `{app_to_app: [], including_resources: []}` |
| `critical_path` | object | Ordered node list, length, hop details |
| `migration_waves[]` | object[] | Wave assignments with tracks |
| `sequencing_validation` | object | Assertion results and `sequencing_valid` boolean |
| `coverage` | object | Per-service and portfolio coverage assessment |
| `unresolved_signals[]` | object[] | Signals that produced no edge |
| `alias_collisions[]` | object[] | Ambiguous match keys |
| `closable_gaps[]` | object[] | Prioritized context entries that would improve the graph |
| `excluded_reports[]` | object[] | Reports skipped, with reasons |

### `summary`

```json
{
  "services_analyzed": 0,
  "app_to_app_edges": 0,
  "shared_resource_edges": 0,
  "derived_pairs": 0,
  "external_systems": 0,
  "shared_resources": 0,
  "circular_dependencies_app_to_app": 0,
  "circular_dependencies_including_resources": 0,
  "foundation_services": 0,
  "hub_services": 0,
  "critical_path_length": 0,
  "max_blast_radius": { "node": "", "count": 0, "percent": 0.0 },
  "services_without_dependency_data": 0
}
```

`app_to_app_edges` and `derived_pairs` are separate fields and MUST NOT be summed into a single
"total dependencies" figure anywhere in any artifact.

### `nodes[]`

```json
{
  "id": "settlement-worker",
  "name": "SettlementWorker",
  "kind": "internal | external | resource",
  "resource_kind": "database | file_share | queue | identity_provider | scheduler | service_registry | other | null",
  "platform": null,
  "repo_dir": "ERP_AnyCompanySettlement",
  "report_slug": "settlementworker",
  "per_repo_json_path": "…/settlementworker-mod-report.json",
  "per_repo_md_path": "…/settlementworker-mod-report.md",
  "md_available": true,
  "overall_score": 1.43,
  "tier": "Remediation Required",
  "service_archetype": "stateful-crud",
  "repo_type": "application",
  "repository_priority": "P2",
  "aliases": ["AnyCompany.Settlement.Worker", "settlementworker"],
  "match_keys": { "exact": [], "stripped": [] }
}
```

MOD-sourced fields (`overall_score`, `tier`, `service_archetype`, `repo_type`,
`repository_priority`) are copied **verbatim** from per-repo JSON. This TD never recomputes them.
`external` and `resource` nodes carry `null` for all MOD-sourced fields.

### `edges[]`

```json
{
  "source": "anycompany-billing-gateway",
  "target": "anycompany-settlement-worker",
  "type": "sync | async | shared_db | shared_infra",
  "protocol": "HTTP",
  "coupling": "High | Medium | Low",
  "provenance": "declared | inferred_named | inferred_shared_resource",
  "confidence": "high | medium | low",
  "direction_confidence": "high | medium | low",
  "matched_via": "exact_key | stripped_key | declared | resource_name",
  "md_enriched": true,
  "occurrence_count": 2,
  "evidence": [
    {
      "repo": "anycompany-billing-gateway",
      "question_id": "INF-Q4",
      "source_artifact": "md",
      "raw_text": "The AnyCompany.Billing.Gateway calls AnyCompany.Settlement.Worker via synchronous HTTP."
    }
  ]
}
```

`evidence[]` MUST be non-empty for every edge whose `provenance` is not `declared`. An edge with no
evidence and no declaration is a defect, not a low-confidence finding.

### `graph_metrics`

```json
{
  "per_node": [
    {
      "id": "anycompany-settlement-worker",
      "fan_in": 4,
      "fan_out": 1,
      "fan_in_derived": 3,
      "fan_out_derived": 0,
      "blast_radius_count": 7,
      "blast_radius_percent": 23.3,
      "traverses_resource": true,
      "class": "Foundation | Hub | Leaf | none | Isolated",
      "coupling_pairs": [{ "peer": "anycompany-billing-gateway", "coupling": "Medium", "direction": "inbound" }]
    }
  ],
  "portfolio": {
    "internal_node_count": 0,
    "edge_density": 0.0,
    "largest_scc_size": 0,
    "derived_naming_prefixes": ["anycompany", "erp"]
  }
}
```

### `coverage`

```json
{
  "per_service": [
    { "id": "anycompany-settlement-worker", "edge_count": 5, "inbound_count": 4, "outbound_count": 1,
      "signals_found": 6, "unresolved_signals": 1, "md_available": true, "coverage": "Good" }
  ],
  "portfolio": {
    "good": 0, "partial": 0, "none": 0, "silent": 0,
    "edges_by_provenance": { "declared": 0, "inferred_named": 0, "inferred_shared_resource": 0 },
    "edges_by_confidence": { "high": 0, "medium": 0, "low": 0 },
    "md_available_count": 0,
    "unresolved_signal_count": 0,
    "alias_collision_count": 0
  }
}
```

### `filter_vocab`

```json
{
  "edge_types": ["sync", "async", "shared_db", "shared_infra"],
  "node_kinds": ["internal", "external", "resource"],
  "provenance": ["declared", "inferred_named", "inferred_shared_resource"],
  "confidence": ["high", "medium", "low"],
  "coupling": ["High", "Medium", "Low"],
  "coverage": ["Good", "Partial", "None", "Silent"],
  "node_classes": ["Foundation", "Hub", "Leaf", "Isolated"]
}
```

Emit only the values actually present in this run, preserving the canonical order shown.

---

## HTML Visual Contract

A **single self-contained file**. No external stylesheets, fonts, scripts, or images; no network
fetch at render time. The customer will open it from a local filesystem, frequently without network
access, and a chart library loaded from a CDN would render an empty page.

Where a chart is specified, draw it with inline SVG generated at emit time, not with a charting
library.

### Header

- Title: `Inter-Application Dependencies — {portfolio_name}`
- Subtitle: `{analysis_date} · {N} services · derived from Modernization Readiness Analysis`

### Executive Summary

Prose intro followed by four subsections: **Dependency Landscape**, **Highest-Risk Nodes**,
**Sequencing Implications**, **Coverage Caveat**.

The Coverage Caveat is mandatory and must appear above the fold, not in a footer. It states that the
graph is mined from MOD report prose, that coverage is uneven, and that a service with no edges has
not been shown to be independent.

### Stats card row

| Card | Source |
|---|---|
| Services Analyzed | `summary.services_analyzed` |
| App-to-App Dependencies | `summary.app_to_app_edges` |
| Shared Resources | `summary.shared_resources` |
| Circular Dependencies | `summary.circular_dependencies_app_to_app` |

A fifth card shows `summary.critical_path_length` labelled "Minimum Waves".

### Charts row

- **Coverage Distribution** — donut from `coverage.portfolio.{good, partial, none, silent}`.
- **Top 10 Blast Radius** — horizontal bar from `graph_metrics.per_node`, sorted descending.

### Dependency graph visual

An inline SVG rendering of the graph, or an embedded Mermaid source block in a `<pre>` for estates
above 40 nodes. Internal services, external systems, and resources use three visually distinct node
shapes and a legend. Low-confidence edges render dashed.

### Tab bar

Order: **Dependencies → Services → Shared Resources → Cycles → Waves → Coverage**

| Tab | Columns | Source |
|---|---|---|
| Dependencies | Source, Target, Type, Protocol, Coupling, Confidence, Evidence | `edges[]` |
| Services | Service, Fan-in, Fan-out, Blast Radius, Class, Tier, Priority, Coverage | `graph_metrics.per_node` joined to `nodes[]` |
| Shared Resources | Resource, Kind, Members, Coordination Risk | `shared_resource_clusters[]` |
| Cycles | Cycle, Services, Type, Lowest Confidence, On Critical Path | `circular_dependencies` |
| Waves | Wave, Service, Track, Priority, Blast Radius, Coverage | `migration_waves[]` |
| Coverage | Service, Edges, Signals, Unresolved, Coverage | `coverage.per_service` |

Each tab's table offers a Download CSV control. The Dependencies and Coverage tabs default to
sorting by the column that surfaces risk (Coupling descending; Coverage ascending so gaps appear
first).

### Footer

- `Generated by AWS Transform · Portfolio Inter-Application Dependency Analysis`
- `© {year} Amazon Web Services, Inc. All rights reserved.`

### HTML escaping

Every extracted string — `raw_text`, node names, resource names, protocols — originates in report
text and MUST be HTML-escaped before interpolation. Escape `&`, `<`, `>`, `"`, and `'`. Evidence
prose routinely contains angle brackets, ampersands, and quotes from code snippets and connection
strings.

---

## Error Handling

### Insufficient reports

Fewer than 2 per-repo MOD reports → **terminate**:

`"Inter-app dependency analysis requires at least 2 per-repo MOD reports; found {N} under {path}. Run the Modernization Readiness Analysis across the portfolio first."`

### Unreadable individual report

Record in `excluded_reports[]` as `{path, reason}` and continue. One malformed file must not
discard an otherwise complete analysis. Report the excluded count in `summary` and the sidecar.

### No edges resolved

If zero edges resolve across the whole portfolio, **still emit all four artifacts** and set
`summary.app_to_app_edges: 0`. Do not fail. The report then documents what was searched, what
signals were found, why none resolved, and the `closable_gaps[]` to fix it.

This case must be loud: the Executive Summary states that no dependencies could be resolved, and
that this reflects the analysis input rather than an absence of dependencies in the estate. A silent
empty graph is the exact failure this TD was written to correct, and reproducing it quietly would be
worse than failing.

### Dangling reference

Any `edges[]` endpoint, `migration_waves[]` member, or `coverage.per_service` id that does not
resolve to a `nodes[]` entry → **terminate**, naming the dangling id and the array that held it.

### Sequencing assertion failure

Do not terminate. Emit `sequencing_validation.sequencing_valid: false` with the failed assertions
and the nodes involved, and carry the failure into the Markdown's Sequencing Validation table and the
HTML's Waves tab. A plan presented without its validation failure is worse than no plan.

### Writing into the MOD report directory

Never. If `interapp-dependency-analysis/` cannot be created at the portfolio root, terminate with the
filesystem error rather than falling back to `modernization-readiness-analysis/`.
