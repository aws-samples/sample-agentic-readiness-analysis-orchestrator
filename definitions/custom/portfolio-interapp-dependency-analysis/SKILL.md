---
name: portfolio-interapp-dependency-analysis
description: Build a portfolio inter-application dependency graph from existing per-repo Modernization Readiness (MOD) reports - resolving named service peers, shared databases, file shares, and queues into a directed graph with coupling scores, fan-in/fan-out, blast radius, circular-dependency detection, and dependency-aware migration wave sequencing
version: 1.0.0
---

## Name

Portfolio Inter-Application Dependency Analysis (IAD)

## Objective

Produce a portfolio-level inter-application dependency graph for a service estate that has
already been assessed with per-repo Modernization Readiness Analysis (MOD), answering the two
questions a modernization program cannot start without:

1. **Which applications depend on which** — and through what coupling mechanism (synchronous call,
   asynchronous message, shared database, shared infrastructure).
2. **What breaks when we touch one** — blast radius, foundation services, circular dependencies,
   and the migration wave order those constraints imply.

This TD consumes MOD reports only. It does **not** re-scan source code, so it runs in minutes
against an existing MOD export rather than hours against a repository estate.

## Summary

The managed Portfolio MOD TD (`AWS/portfolio-modernization-readiness-analysis`) already contains
correct dependency-graph mathematics in its Step 4. In practice that step emits an empty graph,
because of a structural input gap:

- Its primary input is `dependency_overrides` from `additionalPlanContext`, which most engagements
  do not supply.
- Its documented fallback is to infer dependencies "from individual MOD report findings" — but the
  portfolio `findings[]` projection it reads **strips** `description`, `gap`, and `recommendation`
  (see the managed output contract: *"Fields NOT present in the portfolio `findings[] `entry"*).
  Those three fields are the only place integration prose lives.
- Its output contract additionally forbids reading per-repo Markdown: *"The portfolio TD SHALL NOT
  fall back to parsing per-repo MD or HTML."*

The result is a report whose `dependency_map` reads
`{"source": "inferred", "dependencies": [], "foundation_services": [], "circular_dependencies": []}`
on a portfolio of any size, which in turn degrades `roadmap_phases` to generic calendar buckets and
leaves `parallel_execution_tracks[].dependencies` empty.

This TD closes that gap. It reads the **unstripped per-repo MOD artifacts** — JSON
`findings[].description` / `.gap` / `.recommendation` / `.evidence` as the structured primary
source, and per-repo Markdown as enrichment where the Markdown names peers the JSON compresses
away. It resolves the service names it finds against an alias registry built from the portfolio's
own repository inventory, then applies the managed Step 4.1–4.5 graph mathematics to the resulting
edge set.

Every edge carries provenance and confidence, and the report states its own coverage explicitly, so
the graph is something the customer validates rather than something they are asked to trust.

**Pipeline:**

| Step | Purpose | Performed by |
|---|---|---|
| 0 | Read `additionalPlanContext` | you |
| 1 | Discover per-repo MOD reports | `scripts/prepare_corpus.py` |
| 2 | Build the alias registry | `scripts/prepare_corpus.py` |
| 3 | Extract candidate integration signals | `scripts/prepare_corpus.py` |
| 4 | **Classify signals into typed edges** | **you — this is the judgment step** |
| 5 | Compute graph metrics | `scripts/render_report.py` |
| 6 | Cluster shared resources | `scripts/render_report.py` |
| 7 | Assess coverage and confidence | `scripts/render_report.py` |
| 8 | Sequence dependency-aware migration waves | `scripts/render_report.py` |
| 9 | Emit the four-artifact bundle | `scripts/render_report.py` |

### ⚠️ Run the two bundled scripts. Do NOT write your own.

`scripts/prepare_corpus.py` and `scripts/render_report.py` ship with this definition and implement
every mechanical step. **Call them; do not reimplement them, and do not write a replacement
processing script.**

This is not a style preference. A portfolio of 100+ repositories is 200+ report files and a report
bundle of several hundred kilobytes. Attempting to read every file and generate every artifact inside
one conversation exhausts the context window before any analysis completes — a verified failure mode,
not a hypothetical one. The scripts exist so the analysis scales to any portfolio size:
`prepare_corpus.py` reduces 200+ files to a small corpus plus batched signal files, and
`render_report.py` guarantees the output contract deterministically.

Your job is Step 4 — deciding which dependencies are real — which is the part that genuinely needs
judgment and the part a script cannot do.

## Entry Criteria

- At least **2** per-repo MOD reports exist beneath the portfolio root. A dependency graph of one
  node is meaningless; terminate with an error if fewer than 2 are found.
- Each per-repo report contributes a `*-mod-report.json`. The co-located `*-mod-report.md` is
  optional per repo — absence degrades enrichment for that repo but is not fatal.
- Write permission at the portfolio root to create `interapp-dependency-analysis/`.

## Implementation Steps

### Step 0: Read additionalPlanContext

#### 0.1 Fields read by this TD

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `portfolio_name` | string | No | derived (see 0.2) | Base name for all four output artifacts. |
| `context` | string | No | — | Free-text portfolio framing. Used to interpret ambiguous service names and to frame narrative sections. |
| `dependency_overrides` | object[] | No | — | Authoritative declared edges. Each entry: `{source, target, type, description}` where `type ∈ {sync, async, shared_db, shared_infra}`. Supplied edges are never overridden by extracted ones. |
| `service_aliases` | object | No | — | Map of canonical service name → list of alternate names. Seeds the alias registry (Step 2) with customer knowledge the reports cannot supply. |
| `external_systems` | string[] | No | — | Names of known third-party or out-of-scope systems. Forces classification as external nodes rather than unresolved names. |
| `critical_services` | string[] | No | — | Services whose blast radius should be called out regardless of computed rank. |

#### 0.2 Deriving `portfolio_name` when absent

Apply in order, and record which rule fired in the metadata sidecar's `portfolio_name_source`:

1. If `portfolio_name` is supplied, use it verbatim → `supplied`.
2. Otherwise, if an existing portfolio MOD report is discoverable (a
   `*-portfolio-mod-report.json` anywhere beneath the portfolio root), read its
   `metadata.portfolio_name` → `derived_from_portfolio_mod`.
3. Otherwise, use the basename of the portfolio root directory, lowercased, with whitespace and
   underscores collapsed to single hyphens → `derived_from_workdir`.
4. Otherwise, use the literal `portfolio` → `default`.

Never derive the name silently. The filenames carry it, so a derived name is indistinguishable
from a chosen one without the sidecar field.

#### 0.3 Fields NOT read by this TD

`team_size`, `timeline_constraint`, `budget_constraint`, `compliance_requirements`,
`risk_tolerance`, `preferences`. Those shape the Execution Plan (EBA) TD, not a dependency graph.
If present, ignore them without warning.

### Steps 1-3: Build the corpus (run the script)

The two scripts ship inside this definition under `scripts/`. **If they are not present on disk in
your working directory, write them there once from the definition contents, then run them.** Do not
rewrite them from memory and do not "improve" them — reproduce them byte-for-byte, or run them from
wherever the definition was materialized.

```bash
python3 -I scripts/prepare_corpus.py <portfolio-root>
```

**Run this even if `<portfolio-root>/.iad-work/` already exists.** A corpus left over from an earlier
run may predate changes to the reports or to the extraction rules, and reusing it silently analyses
stale input. The script is deterministic and fast, and it clears old signal batches before writing
new ones, so re-running is always the safe choice.

This performs discovery, the alias registry, and candidate-signal extraction, and writes:

| Path | Contents |
|---|---|
| `<portfolio-root>/.iad-work/corpus.json` | Service inventory, derived naming prefixes, exact and stripped match keys, alias collisions, excluded reports, and the list of signal batches |
| `<portfolio-root>/.iad-work/signals/batch-NNN.json` | Candidate integration snippets, batched to a readable size |

The script fails with a clear message if fewer than 2 per-repo MOD reports exist, and records
unreadable or non-MOD reports in `excluded_reports[]` without failing the run.

What it does, in reference terms:

- **Step 1 — discovery.** Globs `*-mod-report.json` at any depth, excluding `*-portfolio-*`
  roll-ups. Directory depth and layout are irrelevant; structure comes from file contents.
- **Step 2 — alias registry.** Collects aliases from `repo_name`, `repo_dir`, report slug, and
  project/assembly names found in `findings[].evidence.file`. Derives organization and system
  prefixes from the inventory itself (any leading token shared by 3+ entries), then emits both exact
  and prefix/suffix-stripped match keys. Colliding keys are recorded in `alias_collisions[]` and
  excluded from automatic resolution.
- **Step 3 — candidate extraction.** Keeps only prose that could carry a dependency, from the
  per-repo JSON `findings[].description` / `.gap` / `.recommendation` / `.evidence.file`,
  `top_gaps[]`, `decomposition_strategy.effort_factors`, and
  `metadata.archetype_justification` — plus the per-repo Markdown `#### {QID}` Finding / Gap /
  Evidence rows for the high-yield questions. `recommendation` is mined only on high-yield
  questions, because recommendations describe systems that do not yet exist.

> **Markdown is read on purpose.** The managed Portfolio MOD contract forbids it, but the
> named-peer prose exists nowhere else. The pattern, shown on the same repo and question:
> the JSON said *"Inter-service communication is entirely synchronous HTTP"* (mechanism, no peers)
> while the Markdown said *"The AnyCompany.Billing.Gateway calls AnyCompany.Settlement.Worker via synchronous HTTP"*
> (two named peers and a direction). JSON stays authoritative for structured fields; Markdown is
> authoritative for who the peers are. Mark any Markdown-derived edge `md_enriched: true`.

Read `corpus.json` first, then work through the batches in Step 4.

### Step 4: Resolve Signals Into Typed Edges

**This is your step, and you must do it yourself.** Read `corpus.json`, then read each
`signals/batch-NNN.json` **in turn** and classify its snippets before opening the next one.

#### Three rules that decide whether this step succeeds

**1. Append to a working file after every batch, before opening the next one.**

```bash
cat >> <portfolio-root>/.iad-work/working-edges.jsonl << 'EOF'
{"type": "sync", "source": "...", "target": "...", ...}
EOF
```

One JSON object per line. Finish the batch, append, then move on. Holding twelve batches of findings
in memory and writing at the end loses everything if the step is interrupted.

**2. Do NOT delegate batch classification to a subagent.**

Research-only subagents cannot write files. If you hand a batch to one, its findings come back as
prose and are silently lost unless you write them yourself — and a batch that is "analyzed" but never
appended is indistinguishable, in the final report, from a batch whose services genuinely have no
dependencies. Verified failure: batches 4–8 of a twelve-batch run were handed to research-only
subagents and left no trace in the working file, while the run appeared to be progressing normally.

Classify every batch in your own turn. It is slower and it is correct.

**3. Account for every service, including the ones with nothing.**

Before rendering, confirm each batch's services appear either as an edge endpoint or in
`unresolved_signals[]`. A service that had signals but produced neither was skipped, not found
independent. `render_report.py` checks this and warns, but it cannot recover the work — so check
before you render.

Process batches one at a time. Reading several at once is how this step runs out of context on a
large portfolio, and a partial classification is much worse than a slower complete one.

For each snippet, decide: does it describe a real dependency, what kind, in which direction, and
against which node? Read `references/01-extraction-signals.md` for the signal catalogue, the
sentiment-versus-mechanism rules, the rejection lists, and external-system classification. The
subsections below define the edge model you are populating.

#### 4.1 Edge types

Carried forward unchanged from the managed TD's Step 4.1, including the modernization implications:

| Type | Description | Modernization implication |
|---|---|---|
| `sync` | Synchronous REST / SOAP / gRPC / RPC call | Tight coupling — source must be modernized after or concurrently with target |
| `async` | Message queue, event bus, pub/sub | Loose coupling — services can be modernized more independently |
| `shared_db` | Two or more services access the same database | Database migration affects all consumers — coordinate carefully |
| `shared_infra` | Common gateway, auth system, scheduler, file share, load balancer | Shared infrastructure changes affect all dependents |

#### 4.2 Mechanism classification

Classify from `protocol` and `mechanism_hint`, in this precedence order:

1. Named queue, topic, or bus technology (MSMQ, SQS, SNS, EventBridge, Kafka, RabbitMQ, Service
   Bus) → `async`.
2. Named synchronous protocol (HTTP, REST, SOAP, WCF, gRPC, XMLHttpRequest, COM+, NetTcp) →
   `sync`.
3. A shared named database catalog, schema, linked server, or OLEDB/ODBC data source → `shared_db`.
4. A shared named file share, scheduler, identity provider, service registry, or gateway →
   `shared_infra`.
5. Otherwise → do not emit an edge. Record as an unresolved signal (4.5).

Phrasing like *"no messaging infrastructure exists; communication is entirely synchronous HTTP"*
is a **positive** `sync` signal, not an absence of signal. MOD question `INF-Q4` asks whether async
messaging exists, so its findings routinely describe real synchronous coupling while scoring the
absence of async. Read the mechanism, not the sentiment.

#### 4.3 Direction

- If the prose names an actor and an object (*"A calls B"*, *"A depends on B"*, *"A consumes B"*),
  the edge runs actor → object.
- If the reporting repo is clearly the consumer (*"calls three external SOAP endpoints"*), the edge
  runs reporting repo → named peer.
- For `shared_db` and `shared_infra`, emit an edge from each participating service **to the shared
  resource node**, not between the services. Service-to-service coupling through a shared resource
  is then derived in Step 6, where it belongs.
- If direction is genuinely undeterminable for a `sync` or `async` signal, emit the edge from the
  reporting repo and set `direction_confidence: "low"`.

#### 4.4 Node classification

Resolve each candidate name against the alias registry:

| Outcome | Node kind | Notes |
|---|---|---|
| Matches an inventory entry on an exact key | `internal` | confidence `high` |
| Matches an inventory entry on a stripped key only | `internal` | confidence `medium`; record `matched_via: "stripped_key"` |
| Matches an `external_systems` entry from context | `external` | confidence `high` |
| Matches a known third-party platform (see `references/01-extraction-signals.md` §4) | `external` | confidence `medium` |
| Is a database catalog, file share, queue, or identity provider | `resource` | typed by subkind |
| Matches nothing | — | unresolved signal (4.5) |

External and resource nodes belong in the graph. In a legacy estate most real coupling runs through
a shared SQL Server database, a UNC file share, or a third-party platform rather than through an
app-to-app API call, and a graph that omits them understates blast radius badly. They are kept
structurally and visually distinct from app-to-app edges throughout the report.

#### 4.5 Unresolved signals

A signal that produced candidate names but no edge is **not discarded**. Record it in
`unresolved_signals[]` with `source_repo`, `question_id`, `candidate_names[]`, `raw_text`,
`resolved_target` (the node it *did* resolve to, or `null`), and a `reason`.

**The reason determines the remedy, so the reasons must not be conflated:**

| `reason` | What happened | Closable by |
|---|---|---|
| `no_alias_match` | The candidate name resolved to nothing in the registry. | A `service_aliases` or `external_systems` entry. |
| `ambiguous_alias` | The name's match key collided across 2+ inventory entries (2.3). | A `service_aliases` entry disambiguating the collision. |
| `mechanism_unclear` | **The name resolved fine**, but no coupling mechanism could be classified. | A `dependency_overrides` entry — nothing about naming will fix it. |
| `generic_name` | The candidate was a bare role word or technology name (see `references/01-extraction-signals.md` §3.1, §3.7). | Nothing. Expected noise; exclude from closable gaps. |

Only `no_alias_match` and `ambiguous_alias` belong in the Step 7.3 closable-gaps list as naming
fixes. Reporting a `mechanism_unclear` signal as an alias gap sends the customer to add an alias for
a service the analysis already recognized, which cannot help and erodes trust in the whole gap list.
`generic_name` signals are excluded from the gap list entirely and reported only as an aggregate
count.

Verified failure mode: on a portfolio of roughly a hundred repositories, conflating these reasons put `WebAPI` at the top of
the closable-gaps list with hundreds of "blocked signals" — a bare role word that no alias can
resolve — while real unresolved services sat below it.

#### 4.6 Deduplication and provenance

Merge edges sharing the same `(source, target, type)` triple. On the merged edge:

- `evidence[]` accumulates every contributing `{repo, question_id, raw_text, source_artifact}`.
- `occurrence_count` is the number of contributing signals.
- `provenance` is the strongest contributor, ordered `declared` > `inferred_named` >
  `inferred_shared_resource`:

| Provenance | Meaning |
|---|---|
| `declared` | From `dependency_overrides`. Customer-asserted; never overridden. |
| `inferred_named` | Extracted prose named a peer that resolved to a node. |
| `inferred_shared_resource` | Derived from co-participation in a shared database, share, or queue. |

- `confidence` is `high` / `medium` / `low` from the weakest link in the chain (name-match
  confidence, direction confidence, mechanism certainty). A `declared` edge is always `high`.

Never silently promote confidence on repetition. Ten medium-confidence stripped-key matches of the
same name remain medium — they share one systematic failure mode, so repetition is not independent
corroboration.

### Step 4 output: write `edges.json`

When you have classified every batch, write your decisions to
`<portfolio-root>/.iad-work/edges.json`:

```json
{
  "portfolio_name": "anycompany",
  "portfolio_name_source": "supplied",
  "context": "free text from additionalPlanContext",
  "extra_nodes": [
    {"name": "AnyCompanyLedgerDb", "kind": "resource", "resource_kind": "database", "platform": null},
    {"name": "Vendor Platform", "kind": "external", "resource_kind": null, "platform": "Vendor"}
  ],
  "edges": [
    {"source": "anycompany-billing-gateway", "target": "anycompany-settlement-worker",
     "type": "sync", "protocol": "HTTP",
     "provenance": "inferred_named", "confidence": "high",
     "direction_confidence": "high", "matched_via": "exact_key",
     "md_enriched": true,
     "evidence": [{"repo": "anycompany-billing-gateway", "question_id": "INF-Q4",
                   "source_artifact": "md",
                   "raw_text": "The AnyCompany.Billing.Gateway calls AnyCompany.Settlement.Worker via synchronous HTTP."}]}
  ],
  "unresolved_signals": [
    {"source_repo": "billing-api", "question_id": "APP-Q3",
     "candidate_names": ["AnyCompanyRatingEngine"], "resolved_target": null,
     "reason": "no_alias_match", "raw_text": "..."}
  ],
  "closable_gaps": [
    {"gap": "AnyCompanyRatingEngine not resolved", "blocked_signals": 12,
     "recommended_entry": "service_aliases: map 'AnyCompanyRatingEngine' to its repo, or add to external_systems"}
  ]
}
```

Rules for this file:

- **The coupling kind goes in `"type"`, not `"edge"`.** It must be exactly one of `sync`, `async`,
  `shared_db`, `shared_infra`. The renderer also accepts `"edge"` as a synonym, but `"type"` is the
  contract — write that. An edge with no recognizable type is a **fatal** error listing every
  offender; the renderer will not silently drop it.
- `source` and `target` accept a report slug, a repo name, or any alias — the renderer resolves them
  against the registry. An endpoint that resolves to nothing is a **fatal** error naming the edge, so
  only reference nodes you declared in `extra_nodes` or that exist in the inventory.
- Declare every external system and shared resource in `extra_nodes` before referencing it.
- `evidence[]` must be non-empty for every edge whose `provenance` is not `declared`. Quote real
  report text in `raw_text`.
- Emit `shared_db` and `shared_infra` edges from each service **to the resource node**, never
  between the services. The renderer derives service-to-service pairs from cluster membership in
  Step 6; emitting them yourself double-counts.
- Add every `dependency_overrides` entry from `additionalPlanContext` as an edge with
  `provenance: "declared"`.
- Carry `unresolved_signals[]` and `closable_gaps[]` through — they become the report's coverage and
  gap sections, which are what make the next run better. Order `closable_gaps[]` by
  `blocked_signals` descending, and include only `no_alias_match` and `ambiguous_alias` reasons as
  naming fixes.

### Steps 5-9: Compute and emit (run the script)

```bash
python3 -I scripts/render_report.py <portfolio-root>
```

This reads `corpus.json` and your `edges.json`, performs every remaining computation, and writes the
four-artifact bundle. Specifically:

- **Step 5** — coupling scores per ordered pair; fan-in/fan-out with derived subtotals tracked
  separately; blast radius by breadth-first traversal of **inbound** edges, counting internal nodes
  but traversing through resource and external nodes; Foundation / Hub / Leaf / Isolated
  classification; Tarjan strongly-connected components run twice (app-to-app only, and including
  resources); and the critical path over the cycle-condensed graph.
- **Step 6** — shared-resource clusters with coordination risk, derived service pairs, and the
  oversize guard that drops any cluster exceeding 40% of the portfolio as a generic-name extraction
  error. Observed and derived counts are reported separately and never summed.
- **Step 7** — per-service and portfolio coverage (`Good` / `Partial` / `None` / `Silent`), and edge
  counts by provenance and confidence.
- **Step 8** — wave assignment (Wave 0 for foundations, hubs, cycles, and high-risk clusters; then
  topological waves; then Wave ∞ for the unsequenceable), parallel tracks per wave, and the four
  sequencing assertions. A failed assertion is reported, never silently reordered away.
- **Step 9** — the Markdown, JSON, self-contained HTML, and metadata sidecar, per
  `references/03-report-template.md` and `references/04-output-contract.md`.

The script prints a one-line summary. Confirm all four files exist before reporting success, and
report the printed counts rather than re-deriving them.

Do **not** hand-write any of these artifacts, and do not post-process them. If a number looks wrong,
the fix belongs in `edges.json`, not in the rendered output.

## Reference Files

| File | Contents |
|---|---|
| `scripts/prepare_corpus.py` | Steps 1–3. Discovery, alias registry, batched candidate-signal extraction. |
| `scripts/render_report.py` | Steps 5–9. Graph metrics, clustering, coverage, waves, four-artifact bundle. Its docstring is the authoritative `edges.json` schema. |
| `references/01-extraction-signals.md` | **Read before Step 4.** High-yield MOD question IDs, signal catalogue, sentiment-vs-mechanism rules, rejection lists, external-system classification. |
| `references/02-graph-metrics.md` | Definitions the renderer implements — coupling, blast radius, SCC, critical path, clustering, waves. Read when interpreting output or explaining a number. |
| `references/03-report-template.md` | Markdown report section order and table shapes. |
| `references/04-output-contract.md` | JSON contract, HTML visual contract, error handling. |

## Constraints and Guardrails

- **Use the bundled scripts; never write a replacement.** `scripts/prepare_corpus.py` and
  `scripts/render_report.py` implement Steps 1–3 and 5–9. Generating your own processing script at
  portfolio scale exhausts the context window before producing anything — a verified failure, not a
  hypothetical one. Your contribution is Step 4.
- **Process signal batches one at a time.** Do not read all of `signals/` at once.
- **Read-only.** Do not modify source code, per-repo MOD reports, or the existing portfolio MOD
  report. The only writes are the four new artifacts in `interapp-dependency-analysis/`.
- **Stay on the current branch.** This is analysis only. Do not create, switch, or check out any
  git branch. Do not commit.
- **No re-scanning repositories.** This TD consumes MOD reports. If repository source is present at
  the portfolio root, ignore it — scanning it would change the runtime from minutes to hours and
  silently alter the analysis contract.
- **Never fabricate an edge.** Every edge traces to at least one `evidence[]` entry quoting real
  report text, or to a `dependency_overrides` entry. An edge with no evidence is a bug.
- **Never fabricate a node.** Nodes come from the inventory, from `external_systems`, from the
  third-party list, or from named resources in evidence. Do not invent a plausible service.
- **Prefer a named gap to a guessed edge.** Ambiguous aliases, unclear mechanisms, and
  undeterminable direction go to `unresolved_signals[]` with a closable-gap recommendation.
- **Report raw and derived edge counts separately.** Shared-resource clustering generates
  combinatorially many derived edges; a combined total misrepresents the finding density.
- **`Silent` never reads as independent.** Every presentation of a zero-edge service states that
  the reports did not describe its integrations.
- **Do not re-derive MOD scores or findings.** Scores, tiers, severities, and pathways are read
  verbatim from per-repo JSON. This TD adds a dependency dimension; it does not re-assess
  readiness.
