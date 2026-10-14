# Markdown Report Template

> **Purpose:** Loaded by the Portfolio Inter-Application Dependency (IAD) TD at Step 9. Defines the
> Markdown artifact's section order, heading text, and table shapes. Headings are fixed — downstream
> tooling and the HTML renderer key on them.

Emit sections in the order below. Where a section has no content, emit the heading and a single
explanatory line rather than omitting it: a missing section is indistinguishable from a section the
analysis forgot, and the empty cases here are themselves findings.

---

## Required Section Order

```markdown
# Portfolio Inter-Application Dependency Report: {portfolio_name}

**Analysis date:** {YYYY-MM-DD}
**Services analyzed:** {N}
**Source:** Per-repo Modernization Readiness Analysis reports
**Edge provenance:** {D} declared · {IN} inferred (named) · {ISR} inferred (shared resource)

---

## Executive Summary

{3-5 paragraphs. Must state, in plain prose: how many services were analyzed; how many
application-to-application dependencies were found; how many shared resources couple services
together; the single largest blast radius and which service or resource holds it; how many circular
dependencies exist; the minimum number of sequential migration waves the topology requires; and how
complete the coverage is. State the coverage limitation here, not only in the coverage section —
a reader who stops after the summary must still know what the graph does not cover.}

## Dependency Overview

| Metric | Value |
|---|---|
| Services analyzed | {N} |
| Application-to-application edges (observed) | {N} |
| Shared-resource edges (observed) | {N} |
| Derived service-to-service pairs (from shared resources) | {N} |
| External systems identified | {N} |
| Shared resources identified | {N} |
| Circular dependencies (app-to-app) | {N} |
| Circular dependencies (including shared resources) | {N} |
| Foundation services | {N} |
| Hub services | {N} |
| Critical path length (minimum waves) | {N} |
| Services with no dependency data | {N} |

> Observed and derived edge counts are reported separately and are never summed. A shared resource
> with N consumers mechanically implies N·(N−1) service pairs; combining the two would overstate the
> number of distinct findings.

## Application Dependency Map

### Application-to-Application Dependencies

| Source | Target | Type | Protocol | Coupling | Provenance | Confidence | Evidence |
|---|---|---|---|---|---|---|---|
| {service} | {service} | {sync\|async} | {protocol} | {High\|Medium\|Low} | {provenance} | {confidence} | {repo}:{question_id} |

Ordered by coupling descending, then source name.

### Dependencies on External Systems

| Source | External System | Platform | Type | Protocol | Confidence | Evidence |
|---|---|---|---|---|---|---|

### Dependency Graph

{A Mermaid `flowchart LR` of the graph. Internal services as default nodes, external systems as
`[/name/]`, resources as `[(name)]`. Edge labels carry the type. Use `-.->` for low-confidence
edges and solid arrows otherwise.

If the graph exceeds 40 nodes, emit one diagram per wave instead of a single unreadable diagram, each
under a `#### Wave {n}` subheading, and say so in a line above them.}

## Service Dependency Metrics

| Service | Fan-in | Fan-out | Blast radius | Blast radius % | Class | Coverage |
|---|---:|---:|---:|---:|---|---|

Ordered by blast radius descending. `Class` ∈ {Foundation, Hub, Leaf, —, Isolated}.
`Coverage` ∈ {Good, Partial, None, Silent}.

### Foundation Services

{Services many depend on and that depend on little. For each: fan-in, blast radius, and one
sentence on why it must be modernized before its dependents.}

### Hub Services

{High fan-in AND high fan-out. For each: why it is the highest-risk class of node in the estate —
it cannot be moved early (it depends on much) or late (much depends on it).}

## Shared Resource Clusters

| Resource | Kind | Members | Coordination risk | Writers | Readers |
|---|---|---:|---|---:|---:|

Ordered by member count descending. For each High-risk cluster, add a subsection naming every member
service and the recommended decoupling approach (schema split, read model extraction, API
interposition).

## Circular Dependencies

### Application-to-Application Cycles

{For each cycle: participating services, the edges forming it, the lowest edge confidence, and
whether any member is on the critical path. If none: "No application-to-application circular
dependencies were detected in the resolved graph." plus a one-line coverage caveat.}

### Cycles Through Shared Resources

{Same shape. These are coordination constraints, not call loops — state that distinction explicitly
so the remedy is not misread.}

## Critical Path

{The longest dependency chain, node by node, with each hop's edge type and confidence. Then: "This
chain sets a floor of {N} sequential migration waves. Adding delivery capacity parallelizes work
within a wave; it cannot reduce the number of waves."}

## Dependency-Aware Migration Waves

### Sequencing Principles

{Numbered list: dependencies before dependents; cycles and foundations first; shared-resource
coordination before member migration; services lacking dependency data sequenced by priority and
flagged.}

### Wave 0 — Foundation and Blockers

| Service | Reason | Fan-in | Blast radius | Priority |
|---|---|---:|---:|---|

### Wave {n}

| Service | Track | Dependencies satisfied in | Priority | Blast radius | Coverage |
|---|---|---|---|---:|---|

{Repeat per wave. Then the parallel tracks for that wave:}

**Parallelizable tracks in Wave {n}:**

| Track | Services | Count | Depends on waves |
|---|---|---:|---|

### Wave ∞ — Unsequenceable

{Services that could not be placed, and the cycle preventing placement. If none, say so.}

### Sequencing Validation

| Assertion | Result |
|---|---|
| Dependencies placed no later than dependents | {Pass\|Fail} |
| Every service placed exactly once | {Pass\|Fail} |
| Wave count ≥ critical path length | {Pass\|Fail} |
| No Wave 0 service duplicated in later waves | {Pass\|Fail} |

{If any Fail, name the violating nodes. Do not reorder to force a pass.}

## Coverage and Confidence

### Portfolio Coverage

| Coverage | Services | Meaning |
|---|---:|---|
| Good | {N} | 3+ resolved edges, or a declared edge |
| Partial | {N} | 1–2 resolved edges |
| None | {N} | Integration signals found but unresolved |
| Silent | {N} | No integration signals in the reports |

> **`Silent` does not mean independent.** It means these services' MOD findings did not describe
> their integrations. MOD describes integrations incidentally, while scoring something else, so
> silence is a reporting gap rather than an architectural fact. Do not treat a Silent service as a
> safe first migration candidate on the strength of this report alone.

### Edge Confidence Distribution

| Confidence | Edges | |
|---|---:|---|
| High | {N} | Declared, or both endpoints and mechanism named explicitly |
| Medium | {N} | One endpoint inferred, or matched on a stripped name key |
| Low | {N} | Generic peer reference or undetermined direction |

### Unresolved Signals

| Source repo | Question | Candidate name | Reason | Evidence |
|---|---|---|---|---|

{Integrations the reports described but the registry could not place.}

### Alias Collisions

| Match key | Competing services | Recommended `service_aliases` entry |
|---|---|---|

### Derived Naming Prefixes

{The organization and system prefixes derived from the inventory in Step 2.2, so the name-matching
is auditable.}

## Closable Gaps

| Priority | Gap | Blocked signals | Recommended context entry |
|---|---|---:|---|

{Ordered by blocked-signal count descending. Each row gives the exact `service_aliases`,
`external_systems`, or `dependency_overrides` entry to add. Close the top rows and re-run for a
materially better graph.}

## Methodology and Limitations

{State plainly: the graph is mined from MOD report prose written to score readiness, not to document
architecture; coverage is therefore uneven by construction; no repository source code was scanned;
absence of an edge is not evidence of independence; and `dependency_overrides` is the supported path
for authoritative data. Name the count of reports consumed and any excluded.}

## Appendix: Services Analyzed

| Service | Repo directory | Tier | Score | Archetype | Priority | MD available |
|---|---|---|---:|---|---|---|
```

---

## Table Discipline

- Every table emits its header row and alignment row even when it has no data rows; follow an empty
  table with one italic line explaining the emptiness.
- Escape pipe characters in any extracted prose before placing it in a cell. Evidence strings come
  from report text and will contain them.
- Truncate evidence cells to 160 characters with a trailing ellipsis. The full text lives in the
  JSON artifact's `evidence[]`.
- Never emit a cell containing only `N/A` where a real value is derivable. `0` and `None` are
  values; `N/A` means the question does not apply to that row.
