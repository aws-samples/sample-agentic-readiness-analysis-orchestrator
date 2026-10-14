# The Deliverable: Shape and Mapping

What a delivered modernization assessment actually looks like, and how findings become waves and programs. Read this when you are building or reviewing the deliverable rather than running the tools.

---

## 1. The artifact set

Four layers, produced by three engines plus a human layer.

**Layer 1 — per-repo readiness.** One run per repository, each yielding a four-file bundle: `<slug>-{ara,mod}-report.{json,md,html,metadata.json}`. **The JSON is canonical; the Markdown carries prose the JSON compresses away.** That asymmetry matters more than it sounds — see §2 step 3.

**Layer 2 — portfolio roll-up.** One run, same four-file bundle. Adds `repositories[]`, portfolio-level findings (`PORT-<TYPE>-Qn`), `recommended_actions[]` (the programs), pathways, roadmap phases, and a `dependency_map`.

**Layer 3 — dependency graph.** A separate bundle in its own directory parallel to the readiness directory and forbidden from writing into it: `.md`, `.json` (canonical), self-contained `.html`, `.metadata.json` sidecar, and `.diagrams.mmd` (Mermaid source extracted so large graphs do not inline). Plus a scratch tree holding the corpus, batched signal files, the edge set, a working append-log, and a snapshot of the previous iteration.

**Layer 4 — the human join.** Generated locally with no network at render time: a static wave plan for print and review, and a navigable dashboard with client-side what-if. **No engine emits the joined view.** This layer is where the advice lives.

Two structurally significant extras worth copying into any engagement:

- **A mechanical baseline kept side by side with the real run.** A regex-only lower bound, retained as proof the extraction approach produces a non-empty graph. Prove the approach before paying for a cloud run.
- **A validation pair:** one script to prove extraction works at all, and one to generate a mechanical edge set so the renderer can be exercised with no agent in the loop.

And ship the capability, not just the report: a quickstart, an annotated configuration template, a reference doc, and the definition source. The customer should be able to re-run it.

---

## 2. The mapping chain, with the key each step joins on

```
source code
  └─(per-repo analysis)→ per-repo report            key: (analysis_type, question_id)
        ├─(portfolio roll-up)→ portfolio report     key: repo_name
        └─(dependency analysis, reads the UNSTRIPPED per-repo artifacts)
              ├─ corpus + alias registry             key: normalized match_keys {exact, stripped}
              ├─ typed edges  ← JUDGEMENT            key: canonical node id
              ├─ metrics + resource clusters
              ├─ coverage grading
              └─ dependency-aware waves
                    └─(human join)→ wave plan / dashboard / programs
                                                     key: repo_name == node name (kind=internal)
```

1. **Finding → question.** Per-repo findings carry `question_id`, `category_id` and an internal numeric score; `evaluations[]` carry a status. The two arrays **partition** the rubric — disjoint, and together covering every question. **The join key is the `(analysis_type, question_id)` pair, never the question id alone**, because ARA and MOD both have a `DATA` short code and the ids collide.
2. **Per-repo → portfolio.** Keys on `repo_name`. The real constraint: the portfolio `findings[]` projection **strips `description`, `gap` and `recommendation`** — the only fields where integration prose lives. That single fact is why the dependency step reads per-repo artifacts directly instead of the roll-up.
3. **Prose → integration signal.** Mined from per-repo JSON `findings[].description` / `.gap` / `.recommendation` / `.evidence`, with the per-repo Markdown as enrichment where it names a peer the JSON compressed away. The same finding text that scores "no async messaging" also names *which* service is being called synchronously — **that sentence is a dependency edge.** Findings → edges is a prose-extraction step, not a metadata lookup. Signals are batched per service so a large estate does not exhaust the agent's context; that batching is a verified necessity, not a precaution.
4. **Signal → typed edge.** Candidate names resolve against an alias registry built from the portfolio's own repository inventory plus customer-supplied aliases, using exact and role-suffix-stripped keys (`...Api`, `...Service`, `...Host`, `...Worker` are stripped). Each edge carries `type ∈ {sync, async, shared_db, shared_infra}`, `protocol`, `coupling`, `provenance ∈ {declared, inferred_named, inferred_shared_resource}`, `confidence`, `direction_confidence`, `matched_via`, `occurrence_count`, and **non-empty `evidence[]` quoting the source text**. An undeclared edge with no evidence is a defect, not a low-confidence finding. Non-resolving signals go to `unresolved_signals[]`; ambiguous keys to `alias_collisions[]`.
5. **Edge → node metric.** Fan-in and fan-out counted after dedup, with the derived subtotal recorded separately. **Blast radius is a reverse BFS** over inbound edges — transitive *dependents*, not dependencies — traversing *through* resource and external nodes while not counting them, flagged `traverses_resource`. Classes: **Foundation** (fan-in ≥ 3, fan-out ≤ 1), **Hub** (≥ 3 both), **Leaf** (fan-in ≤ 1, fan-out ≥ 2), **Isolated** (no edges — a coverage statement, not an architecture one).
6. **Resource → cluster.** A resource node's cluster is every service with an edge to it; `coordination_risk` is High at 5+ members or any writer with 3+ readers. **An N-member cluster implies N·(N−1) derived pairs**, which live in a separate `derived_edges[]` and may **never** be summed with observed edges into a "total dependencies" headline. A cluster exceeding roughly 40% of internal services is an extraction bug — a bare technology name admitted as a resource — not a discovery. Shared resource clusters are a first-class grouping: a shared database joining 20+ services is the real migration unit, the structural equivalent of a move group.
7. **Graph → cycles and floor.** Tarjan SCC run **twice** — app-to-app only (call loops) and including resources and derived edges (coordination constraints, which prescribe "split the schema", not "break the call"). SCC condensation then longest path through the resulting DAG gives `critical_path_length` = **the minimum number of sequential waves**, a topology floor that adding teams cannot reduce.
8. **Constraints → waves.** Wave 0 = Foundation nodes ∪ app-to-app SCC members ∪ Hubs ∪ every member of a High-risk cluster. Waves 1..N = topological sort with Wave 0 removed; a node enters the earliest wave where all its dependencies are already placed. **Intra-wave ordering only** is `repository_priority` → descending blast radius → descending score. Wave ∞ = still-cyclic remainder, named rather than forced. Parallel tracks are the connected components of the subgraph induced by a wave.
9. **Readiness ⟂ dependency join.** A single key: portfolio `repositories[].repo_name` against graph `nodes[].name` where `kind == "internal"`. Readiness-sourced fields in the graph (`overall_score`, `tier`, `service_archetype`, `repo_type`, `repository_priority`) are copied **verbatim**; the dependency step never recomputes them. Unjoined services are surfaced as a warning, never dropped silently.
10. **Findings → programs.** Reassembled from **two** artifacts because neither suffices. The portfolio JSON gives the canonical `recommended_actions[]` (acronym, name, status, trigger reason) but no next step and no narrative. The portfolio Markdown gives the richer table — including programs absent from the JSON — plus trigger findings, next step, per-program timing, training priorities, external-support notes, the self-paced learning catalogue, and the `PORT-*-Qn` portfolio findings. **Merge key is acronym-else-name lowercased; JSON status wins on disagreement.**
11. **Gaps → next run.** `closable_gaps[]` names the exact configuration entries that would most improve the graph. That feeds back into the run config. Expect two or three iterations — which is why the previous-iteration snapshot exists.

**Four validation assertions before emit**, and a failure is emitted as `sequencing_valid: false` rather than silently reordered away: every dependency placed no later than its dependent; every node in exactly one wave; wave count ≥ critical path; no Wave 0 node repeated.

---

## 3. Canonical JSON shape of a graph deliverable

Top level: `analysis_type`, `metadata`, `summary`, `filter_vocab`, `nodes[]`, `edges[]`, `derived_edges[]`.

- **`metadata` carries provenance as data**: definition version, how the portfolio name was derived, source analysis type, reports consumed, reports excluded, whether Markdown enrichment was available, and the supplied `context`.
- **`summary` is the executive numbers**: `services_analyzed`, `app_to_app_edges`, `shared_resource_edges`, `derived_pairs`, `external_systems`, `shared_resources`, `circular_dependencies_app_to_app`, `circular_dependencies_including_resources`, `foundation_services`, `hub_services`, `critical_path_length`, `max_blast_radius {node, count, percent}`, `services_without_dependency_data`.
- **`filter_vocab` pre-declares the enum vocabulary** the UI filters on — `edge_types`, `node_kinds`, `provenance`, `confidence`, `coupling`, `coverage`, `node_classes`. **Worth copying into any report you design:** it makes the artifact self-describing instead of forcing the consumer to infer the enums.
- **`edges[]` carries evidence down to the source question**: `{repo, question_id, source_artifact, raw_text}`, plus `provenance`, `confidence`, `direction_confidence`, `matched_via`, `md_enriched`, `occurrence_count`, `coupling`.
- **`nodes[]` carry both graph identity and per-service assessment fields**, plus `aliases` and `match_keys {exact, stripped}` for entity resolution.

**The single most important structural choice is separating `edges[]` (evidenced) from `derived_edges[]` (inferred, typically several times larger).** It keeps a defensible core distinct from a useful-but-weaker expansion.

### Narrative section order — the deliverable's real spine

Executive Summary → Dependency Overview → Application Dependency Map (app-to-app, then external systems and shared resources, then diagrams) → Service Dependency Metrics (foundation services, hub services) → Shared Resource Clusters → Circular Dependencies (app-to-app cycles, then cycles through shared resources) → Critical Path → **Dependency-Aware Migration Waves** (sequencing principles, Wave 0 "Foundation and Blockers", then Waves 1..N, then Sequencing Validation) → Coverage and Confidence (portfolio coverage, edge-confidence distribution, per-service coverage, unresolved signals, alias collisions, derived naming prefixes) → Closable Gaps → Methodology and Limitations.

Note where **Coverage and Confidence** sits: inside the body, before the gaps, not in an appendix.

---

## 4. The wave plan, structurally

`migration_waves[]` of `{wave, track, services[{service, reason, priority, blast_radius, coverage}]}`, plus a sibling `sequencing_validation` object. Rendered as one column per wave — Wave 0 labelled "Foundations and blockers", with a trailing "Unsequenceable" column — each service card showing score, band chip, blast radius count and percent, fan-in/out, high-severity count, and a coverage badge.

**A wave plan cannot be built from readiness scores alone.** It needs all seven of:

1. directed, typed edges — the type determines whether the coupling constrains sequencing at all;
2. a node class per service (Foundation / Hub / Leaf / Isolated);
3. blast radius per service;
4. cycle membership, app-to-app and separately through shared resources;
5. shared-resource clusters with coordination risk;
6. per-service priority and readiness score — used only for *intra*-wave ordering, never to choose the wave;
7. a per-service coverage grade, so placements made on thin evidence render as provisional.

**The load-bearing caveat.** Coverage grades are `Good / Partial / None / Silent`. `None` means integrations *were* described but names did not resolve — fixable with aliases. `Silent` means integrations were never described. **Neither licenses the word "independent."** The wrong reading is actively harmful: a genuinely independent service is the ideal first migration, so a `Silent` service misread as isolated gets promoted to the front of the plan, exactly where an undiscovered dependency does the most damage. Every rendering of a zero-edge service must carry the qualification.

---

## 5. What a real run configuration actually sets

A dependency run reads six optional fields. A real delivered engagement set **three**.

| Field | Set in practice? | Why it matters |
|---|---|---|
| `portfolio_name` | yes | drives every artifact filename |
| `context` (free text) | yes — by far the largest field | the estate framing; see below |
| `external_systems` | yes — a long hand-built vendor and platform list | **the definition intentionally ships no built-in vendor list**, so this is the only way an industry's platforms get recognized |
| `dependency_overrides` | **no** | **the single highest-value field.** Ten declared edges beat a hundred inferred ones |
| `service_aliases` | no | raises resolution on named-but-unmatched signals |
| `critical_services` | no | priority input to intra-wave ordering |

**In the real run, the highest-value field was the one left empty.** Expect that, and say it in the deliverable: the plan stays indicative rather than authoritative until declared edges are supplied.

**What the `context` block should contain**, structurally: estate size and repository count; the language and framework mix with rough proportions; hosting and OS platform; container and serverless adoption or its absence; the data-tier engines and which databases are shared through shared data-access layers; the dominant integration styles (synchronous RPC, batch file exchange over network shares, queueing); legacy component technologies; scheduling and reporting platforms; an explicit **instruction naming the repositories that are internal shared infrastructure** (logging, shared common API, SSO, directory, service registry, installer/config) so they are treated as internal nodes rather than external systems; and a goal statement.

That shared-infrastructure declaration is the highest-leverage sentence in the whole config. **Classify a central logging service as external and the graph collapses into a star; classify it as internal shared infrastructure and it becomes the correct Wave 0 item.**

Explicitly *not* read by a graph run: `team_size`, `timeline_constraint`, `budget_constraint`, `compliance_requirements`, `risk_tolerance`, `preferences`. Those shape an execution plan, not a graph.

---

## 6. The human-judgement gap — this is the advisory job

Everything in this list was supplied by a person. No tool produced any of it.

**A. Deciding which dependencies are real.** The judgement is sentiment-vs-mechanism ("should introduce a queue" is not a queue), direction, named-instance vs bare technology name, and which candidate resolves to which repository. Hand every *mechanical* step to the bundled scripts and do not reimplement them — a large estate is hundreds of report files and attempting it conversationally exhausts context. That is a verified failure, not a hypothetical.

**B. Writing the context.** Estate framing, and especially the internal-shared-infrastructure declaration, is pure customer knowledge.

**C. Supplying declared edges.** The CMDB or integration-catalogue transcription. Nothing in the toolchain produces it. This is the clearest advisor-shaped hole in the chain.

**D. The join itself.** "Readiness answers *how hard is this to move*. Dependency answers *what breaks when we move it*. Neither alone sequences a program; together they do." No engine emits the joined view.

**E. Reconstructing the score model, then using it for what-if.** The arithmetic is derivable and worth validating against the corpus until it reproduces every category score and every overall score exactly: a category score is the mean of its evaluated question scores (findings carry their score; `evaluations` with status `pass` count as full marks; `na` and `not_evaluated_*` are excluded entirely), and the overall score is the mean of the category scores. That turns strategy options into exact projections rather than estimates. On top of it:

- a hand-authored option catalogue, each option naming the specific rubric questions it satisfies, with deliberately **non-uniform targets** — an option that only partly addresses a question is modelled at 3 rather than 4 and flagged "partial" so the projection is not read as a promise;
- documented overlaps, so the combined ceiling is explicitly **less** than the sum of the parts;
- explicit non-claims: effort, cost and duration are **not** modelled (two options can score alike and differ by an order of magnitude in cost), and a projected band is labelled band-only because the authoritative classification also weighs severity counts a projection cannot know.

**F. The counter-intuitive read.** The obvious answer — land on containers — often moves the portfolio *least*, because it satisfies only a few rubric questions, while the cheapest real gains sit in whichever category scores worst. A tool can compute the deltas. Ranking them into "cheap points live in weak categories" is advice.

**G. The act-first shortlist.** A two-axis intersection — low readiness **and** blast radius above a threshold — chosen by a human as the thing on page one.

**H. The action catalogue.** One action per rubric question, aggregated across services **from the analysis's own recommendation text** rather than invented: most-representative recommendation selected by commonest opening then longest, AWS services named in that text extracted against a curated term list and surfaced as "Creates", with effort, priority and phase rolled up by modal value.

**I. Presentation and accessibility judgement.** A two-group membership diagram beats a scatter plot when the data is a membership fact rather than a correlation. Plot the readiness histogram against the **full** rubric range rather than zooming to the data, because the distance to the next band *is* the headline. Status colour is never a colour-only encoding — always icon plus label. Mirror every chart with a sortable table as the colour-independent view.

**J. Proving the approach before spending.** Build the regex-only mechanical lower bound and the agent-free edge generator first. Keep both beside the real bundle in the deliverable.

**K. Operational packaging.** Locate the portfolio root by globbing for report files. `git init` the portfolio directory because the CLI requires it, with the generated report directory and the scratch directory gitignored. Publish the custom definition into the customer's own account, because the registry is per-account. Use an **absolute** path for the work directory. Set the Region explicitly, because `atx custom def` does not read it from AWS config.

---

## 7. Scale expectation

A low-hundreds-of-services portfolio produces roughly a hundred-plus graph nodes, a couple hundred primary edges, and several times that in derived edges. The derived-to-observed ratio of roughly 6:1 is normal and is exactly why the two populations must never be summed.
