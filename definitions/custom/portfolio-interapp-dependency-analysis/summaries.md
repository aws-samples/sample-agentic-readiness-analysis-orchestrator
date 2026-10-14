# Summary

Builds a portfolio inter-application dependency graph from existing per-repo Modernization Readiness
(MOD) reports, without re-scanning source code.

Mines integration prose from the unstripped per-repo artifacts — JSON
`findings[].description` / `.gap` / `.recommendation` / `.evidence`, enriched by per-repo Markdown —
resolves named service peers against an alias registry derived from the portfolio's own repository
inventory, and emits a directed graph of `sync`, `async`, `shared_db`, and `shared_infra` edges.

Produces coupling scores, fan-in/fan-out, blast radius, foundation/hub/leaf classification,
shared-resource clusters, Tarjan circular-dependency detection, critical path length, and a
dependency-aware migration wave plan with parallelizable tracks.

Every edge carries provenance (`declared` / `inferred_named` / `inferred_shared_resource`),
confidence, and the report text it came from. Coverage is assessed per service and reported
explicitly, with a prioritized list of the configuration entries that would most improve a re-run.

Emits four artifacts: Markdown, canonical JSON, a self-contained HTML report, and a metadata sidecar.

Requires at least 2 per-repo MOD reports. Read-only with respect to source code and existing reports.
