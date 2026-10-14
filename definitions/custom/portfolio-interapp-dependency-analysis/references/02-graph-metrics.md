# Graph Metrics Definitions

> **Purpose:** Loaded by the Portfolio Inter-Application Dependency (IAD) TD at Steps 5, 6, and 8.
> Gives precise, worked definitions for coupling scoring, fan-in/fan-out, blast radius, circular
> dependency detection, critical path, shared-resource clustering, and wave sequencing — plus the
> edge cases where a naive implementation produces a confidently wrong number.

The scoring thresholds in §1 and §2 are carried forward unchanged from the managed Portfolio MOD
TD's Step 4, so IAD output stays comparable with a portfolio MOD report that *did* receive
`dependency_overrides`.

---

## 1. Coupling Score

Computed per **ordered service pair** that has at least one edge between them.

| Score | Criteria |
|---|---|
| High | A `sync` edge **and** a `shared_db` edge, **or** 3+ distinct edge types between the pair |
| Medium | A `sync` edge only, **or** exactly 2 distinct edge types between the pair |
| Low | `async` only, **or** `shared_infra` only |

"Distinct edge types" counts members of `{sync, async, shared_db, shared_infra}`, not edge
instances. Four separate `sync` edges between the same pair are one distinct type, so the pair
scores Medium, not High.

Where a pair has edges in both directions, compute each direction separately and report both. The
coupling is not necessarily symmetric: A calling B synchronously while B publishes an event A
consumes is Medium in one direction and Low in the other, and collapsing that to one number loses
the fact that only one direction constrains sequencing.

---

## 2. Per-Node Metrics

### 2.1 Fan-in and fan-out

- **Fan-in** — count of distinct edges terminating at the node.
- **Fan-out** — count of distinct edges originating at the node.

Count after deduplication (SKILL.md 4.6), so one merged edge with eight evidence entries
contributes 1, not 8. Count derived shared-resource edges (Step 6) in the same tally but record the
derived subtotal separately — a service in a 10-member database cluster gains 9 derived edges, which
will otherwise swamp its real call graph.

### 2.2 Foundation and leaf classification

| Class | Criteria | Meaning |
|---|---|---|
| Foundation | fan-in ≥ 3 **and** fan-out ≤ 1 | Many depend on it; it depends on almost nothing. Modernize first. |
| Leaf | fan-in ≤ 1 **and** fan-out ≥ 2 | Almost nothing depends on it; it depends on several. Safe to move late, or early as a pilot. |
| Hub | fan-in ≥ 3 **and** fan-out ≥ 3 | Both. Not in the managed definition; report separately — a hub is the highest-risk node in any estate and must not be silently classed as neither. |
| Isolated | fan-in = 0 **and** fan-out = 0 | **No edges were found.** See §6 — this is a coverage statement, not an architectural one. |

### 2.3 Blast radius

**Definition:** the set of services that could be affected by a change to this node — that is, its
transitive *dependents*.

**Computation:** breadth-first traversal following **inbound** edges (reverse direction), from the
node, over the full graph. Count distinct internal nodes reached, excluding the start node. Express
as both a count and a percentage of total internal nodes.

The direction is the single most common implementation error here. Following outbound edges computes
the node's *dependencies* — what it needs — which is a different and much less useful quantity.
Blast radius answers "if we break this, who notices," so it must run against the arrows.

**Traversal through non-internal nodes:** traverse *through* `resource` and `external` nodes, but do
not count them in the total. Two services sharing a database are genuinely coupled through it, and a
traversal that halts at the resource node will report a blast radius of 0 for a database that fifteen
applications read. Record `traverses_resource: true` on any path that passed through one, so the
number can be interpreted.

**Cycles:** mark nodes visited. A node inside an SCC has a blast radius that includes every other
member of its SCC; that is correct and should not be special-cased away.

### 2.4 Worked example

Edges: `A → B`, `B → C`, `D → C`, `C → DB1`, `E → DB1`.
Internal nodes: A, B, C, D, E (5). Resource node: DB1.

| Node | Fan-in | Fan-out | Blast radius (count) | Blast radius (%) | Class |
|---|---|---|---|---|---|
| A | 0 | 1 | 0 | 0% | Isolated-ish (fan-out 1, no dependents) |
| B | 1 | 1 | 1 (A) | 20% | — |
| C | 2 | 1 | 3 (B, D, A) | 60% | — |
| D | 0 | 1 | 0 | 0% | — |
| E | 0 | 1 | 0 | 0% | — |
| DB1 | 2 | 0 | 4 (C, E, B, A) | 80% | Resource; `traverses_resource` on C/E paths |

`DB1` carries the largest blast radius in the estate despite being nobody's "service." That outcome
is typical of legacy estates and is the main argument for keeping resource nodes in the graph.

---

## 3. Circular Dependency Detection

Run **Tarjan's strongly connected components** algorithm over the directed graph. Any SCC with more
than one member is a cycle. For each cycle record: participating nodes, the edges forming it, each
edge's type and confidence, and the lowest confidence among them.

**Run it twice:**

1. **App-to-app only** — internal nodes, excluding derived shared-resource edges. These are cycles
   of direct calls, and they are unambiguous architectural problems.
2. **Including resource nodes and derived edges** — these cycles are coordination constraints rather
   than call loops. Two services that both read and write `AnyCompanyLedgerDb` form a cycle through it; no
   call exists in either direction, but neither can migrate its schema independently.

Report both, labeled. Merging them invites the reader to treat a shared-database coordination
constraint as a call-graph defect, which prescribes the wrong remedy (breaking a call that is not
there, instead of splitting a schema).

**Confidence discipline:** a cycle whose closing edge is `low` confidence is a *candidate* cycle.
Report it as such. A spurious cycle will push real services into Wave 0 and distort the whole plan,
so the closing edge's confidence must travel with the finding.

---

## 4. Critical Path

1. Remove cycles by condensing each SCC to a single composite node (the standard condensation of a
   directed graph, which is acyclic by construction).
2. Find the longest path through the resulting DAG. Its length in nodes is the **critical path
   length**.
3. The critical path length is the **minimum number of sequential waves** the portfolio requires.
   It is a floor set by topology, not by capacity: adding teams parallelizes work *within* waves and
   cannot reduce the count of waves.
4. Report the path itself, node by node, with each hop's edge type and confidence.

Flag every node that is both on the critical path and inside an SCC. These are the program's
highest-risk items — they cannot be deferred without stalling the sequence, and they cannot be moved
independently.

---

## 5. Shared-Resource Clustering

For each `resource` node, the cluster is every internal service with an edge to it.

| `coordination_risk` | Criteria |
|---|---|
| High | 5+ members, **or** any member writes while 3+ members read |
| Medium | 3–4 members |
| Low | 2 members |

A single-member cluster is not a cluster; record the resource but create no derived edges.

**Derived edges.** Every ordered pair of distinct members gains an edge of type `shared_db` or
`shared_infra` (matching the resource kind), `provenance: "inferred_shared_resource"`, and
`derived_from_cluster: "{resource_name}"`.

**Count discipline.** An N-member cluster generates N·(N−1) derived edges. A 15-member database
cluster alone generates 210. Raw and derived counts must be reported separately everywhere, and no
headline figure may combine them — "we found 290 dependencies" is a misleading description of 80
observed edges plus 210 combinatorial consequences of one shared database.

Read-vs-write participation is often recoverable from the prose ("writes to", "reads from",
"read-only reporting access"). Where it is, record it: a cluster where one service writes and
fourteen read is a far more tractable migration than fifteen mutual writers, and the distinction
changes the recommended remedy from "split the schema" to "extract a read model."

### 5.1 Implausible cluster sizes are a bug signal, not a finding

A cluster containing more than **40%** of the portfolio's internal services is almost always an
extraction error rather than a discovery. Genuine shared resources in a legacy estate are common, but
a single facility used by three-quarters of all applications usually means a bare technology name was
admitted as a resource node (see `references/01-extraction-signals.md` §3.7).

On encountering such a cluster:

1. Re-check the resource against the named-instance test. If the name is a protocol, library, or
   standard rather than a specific instance, **drop the cluster** and record it in
   `excluded_reports[]`-style diagnostics with reason `generic_resource_name`.
2. If the name survives the test, keep the cluster but mark it `oversized: true` and state its size
   explicitly in the report. A genuine 75-member shared database is the most important finding in the
   portfolio and must not be buried.

Never emit derived pairs from a dropped cluster. The derived-pair count scales quadratically, so one
bad cluster can outnumber every real edge by two or three orders of magnitude and make the report
read as substantive when it is noise.

---

## 6. The Zero-Edge Problem

A node with no edges means **one of two completely different things**, and the analysis must never
conflate them:

| Condition | Meaning | Coverage rating |
|---|---|---|
| 0 edges, but integration signals were found and could not be resolved | The reports described integrations; the alias registry could not place them. A **resolution** gap. | `None` |
| 0 edges and 0 integration signals found | The reports never described this service's integrations. A **reporting** gap. | `Silent` |

Neither licenses the conclusion "this service is independent." MOD findings describe integrations
incidentally, in the course of scoring something else; a service whose findings happened not to
mention a peer is not thereby decoupled.

This matters because the wrong reading is actively harmful. A genuinely independent service is an
ideal first migration candidate, so a `Silent` service misread as isolated gets promoted to the front
of the wave plan — the position where an undiscovered dependency does the most damage. Every
rendering of a zero-edge service must therefore carry the qualification, and Step 8 flags such
services as sequenced without dependency information.

---

## 7. Wave Sequencing

### 7.1 Assignment

1. **Wave 0 — Foundation and Blockers:** all Foundation nodes (§2.2), all nodes in any app-to-app
   SCC (§3), all Hub nodes, and every service in a `High` coordination-risk cluster (§5).
2. **Waves 1..N:** topologically sort the remaining internal nodes with Wave 0 removed. A node
   enters the earliest wave in which every one of its dependencies is already placed. Within a wave,
   order by `repository_priority` (P0 → P3), then descending blast radius, then descending
   `overall_score`.
3. **Wave ∞ — Unsequenceable:** nodes whose remaining dependencies still form a cycle. Name the
   node and the cycle instead of forcing a position.

### 7.2 Parallel tracks

Within a wave, partition nodes into connected components over the subgraph induced by that wave.
Each component is a track; distinct tracks have no edges between them and can run concurrently.
Record member services, member count, and the waves the track depends on.

### 7.3 Validation assertions

Assert before emitting, and report the result as `sequencing_valid`:

1. For every edge `X → Y` where neither is in Wave 0: `wave(Y) ≤ wave(X)` — a dependency is
   modernized no later than its dependent.
2. Every internal node appears in exactly one wave, or in Wave ∞.
3. Wave count ≥ critical path length (§4).
4. No Wave 0 node is also listed in Waves 1..N.

If any assertion fails, emit `sequencing_valid: false` with the failing assertion and the nodes
involved. Do not reorder to force the assertion to pass: a failure means the graph contains
something the sequencer could not model, and silently reordering hides it while still producing a
plan the customer would follow.
