# Estate Coverage, Provenance, and the Honest Gaps

Read this when the engagement is estate-wide rather than repository-wide, when you are about to present a conclusion drawn from partial evidence, or when a customer asks for something Transform cannot do.

Nothing here requires any tool beyond AWS Transform and the definitions in this repository. The ideas are a discipline you apply by hand; where the discipline needs machinery that does not exist, §4 says so plainly rather than implying the workflow covers it.

---

## 1. The problem analyses do not solve

Readiness analyses assess **repositories**. An enterprise estate is mostly not repositories — packaged products, databases, appliances, mainframes, schedulers, integration layers, things with no source tree at all. So a portfolio of per-repo reports is an answer about a *minority* of the estate that silently reads as an answer about the estate.

The sharper version of the problem: the customer usually already **has** a finished-looking deliverable — a business case that right-sizes instances and prices a lift-and-shift — and they stop there, because a number tells them where they stand. **A number is not guidance.** Your job is the second sentence: what to do next, and what that costs.

And name the price of the default answer. A rehost later thrown away is money spent raising a ceiling nobody climbed. A component-level target is a different route and usually the cheaper total.

---

## 2. Raw → canonical → advisory

The model worth carrying has three stages, and the discipline is in the seams.

**Read.** One reader per fixed input shape, assembled into a conclusion-free picture. Readers stamp *where every row came from* **and every absence**, and deliberately stamp **no** precedence — deciding which source wins is the next stage's job, not the reader's.

**Resolve.** Several independent judgements over those rows: who is this host, which workloads belong to one application, what does this process configure. This is where rows become *claims*. Every contestable value carries a provenance tier:

| Tier | Weight | Meaning |
|---|---|---|
| `observed` | 0.95 | a tool saw it |
| `customer_asserted` | 0.80 | the customer said it about their own estate |
| `vendor_documented` | 0.60 | a vendor document states the capability |
| `agent_inferred` | 0.35 | a model proposed it |
| `unknown` | **0.0** | a real tier carrying a value with zero weight — it renders, it is citable, it can never win a conflict |

`confidence = BASE × FRESHNESS × TIER`, and comparison is **provenance first**: a fresh guess never outranks a stale observation.

**Guide.** A typed action graph over the accepted picture, deterministic wave derivation, landing comparison under *customer-declared* priorities, and a per-outcome cost of closing the gap.

Two model-level rules travel everywhere:

- **`null`, `[]` and absent are three different statements** — asked-and-none, asked-and-empty, never asked.
- **No figure is computed by the presentation layer.** If a number appears on a page, it came from a named artifact and can be traced there.

### The input channels, and the open door

Four input channels justify a fixed reader because their structure is pinned: a discovery-tool export, an assessment or MPA workbook, modernization-readiness reports, and agentic-readiness reports. Anything else the customer finds useful enters as **inferred** — a draft nothing relies on until a human confirms it. **The four are a spine, not a boundary.**

Do **not** try to re-implement ingestion of the inventory formats (RVTools, CMDB exports, evaluator tools, partner tools, spreadsheet templates). Those formats already collapse into one fixed assessment structure upstream; reading that one artifact gets all of them transitively.

### Evidence precedence, as an ordering rather than a workflow

1. **Discovery is the spine** — hosts, processes, network edges, database inventories, utilization.
2. **Repository assessments attach to *parts* of that spine**, never to the whole of it.
3. **Declared infrastructure is a third kind of claim**, not a substitute for either.
4. **Customer assertions are the only channel that can supply intent and enablement** — and they come **after** the first run, never before, because a human answers the questions the run produced.
5. **Repository registration is plumbing, not evidence.**

⚠️ **The failure this ordering exists to prevent.** A repository registered without an explicit workload hint is stored and joins **nothing** — it answers no question, and it does so invisibly. Eight reports once reached four workloads and answered nothing for days, because the join succeeded at the envelope's top level and failed at the entity level. **Entity resolution, not analysis quality, is the thing that quietly breaks an estate-level assessment.**

---

## 3. The three gates that matter more than any machinery

**Gate 1 — platform readiness and agentic readiness are independent axes, and platform is a ceiling.** A mainframe workload is not "less agent-ready"; it is **capped**. Platform work lowers the price of every rung after it; it does not raise the rung. Both halves of that sentence must ship together: the first alone reads as "don't modernize", the second alone is the overclaim. `bridge-analysis` already quantifies the modernization dividend — frame it as **price reduction**, never as readiness gained.

**Gate 2 — refactor vs reimagine is the customer's axis.** Only a declared *reimagine* intent can support an agentic-readiness increase; refactor cannot change it; missing intent stays `unknown`. **Never inferred.** Keep it distinct from `--agent-scope`, which is about what an agent would be allowed to do inside a repository, and which is infer-else-honor — omitting it does **not** mean read-only.

**Gate 3 — vendor capability with unknown enablement is a question, not a level.** The product supports a machine interface; nobody said whether it is switched on. The honest output is an interview question.

### Declared vs discovered

A declared document (IaC state, a CMDB extract) and an observation are **different claims, and you keep both.** Reconcile and report three populations — **declared**, **corroborated**, and **declared-and-not-observed** — plus containment for each workload. `corroborated` is its own evidence kind, distinct from observed, configured, and customer-declared.

The belief, stated as a rule: **declaration is evidence about intent, observation is evidence about reality, agreement between them is a third and stronger fact, and disagreement is a finding rather than something to resolve by preferring one side.** Preserve conflicts along named dimensions: endpoint, relationship type, direction, temporal scope, application version, interface version.

Two cautions that generalize:

- A platform level read off a hypervisor field once said "not a mainframe" because the collector saw the emulator host. **Key on the signal, never on the level.**
- One shared database rendered as a clique of its consumers turned a few dozen services into thousands of meaningless pairs off a single host. **A shared intermediary must stay a node.**

### The relationship vocabulary, closed

Estate edges — direct call, async/event, shared database, shared infrastructure, batch/file transfer, identity, deployment, human handoff — each carry a direction state (including `unknown_direction`), an evidence kind (observed / configured / corroborated / customer-declared / assessment-inferred / agent-inferred / unknown), and an interpretation status. **Nothing translates an estate edge into an action prerequisite automatically.** A current-state dependency is evidence for planning; it is not itself a prerequisite, and a cycle is a planning conflict to surface rather than dissolve.

### The loop back out

When assessment coverage for a scope is missing, stale, or undated, emit a **handoff** naming the assessment type, the scope, the freshness basis, the expected versioned artifact contract, the external owner, and the path the finished report returns through. **Guidance accelerates external work; it never starts it.** Every recommendation names its owner and the artifact that comes back.

---

## 4. What Transform cannot do alone today

State these as gaps rather than implying the workflow covers them. They are the honest answer to "can you just do the whole estate".

1. **A canonical estate store with a single writer.** Transform produces per-run artifacts. There is no accepted, immutable, versioned estate that successive runs amend, no append-only disposition history, and no digest-bound approval step. Today "accepted" means "a human read the report."
2. **Entity resolution across channels.** Nothing binds a repository report to an application id, a host, or an inventory row. Cross-artifact reads within one workspace are the only join available, and they are *file* reads, not identity resolution. **This is the largest gap and the one that bites first.**
3. **Ingestion of discovery or inventory exports into the same analytical context as the readiness analyses.** A custom definition is closed-world over the files in its working directory, so an export *placed* there can be read — but no managed reader, no fixed field contract, no absence accounting, and no provenance tier comes with it. **Treat any such reading as inferred, not observed.**
4. **A packaged-software / vendor-product channel.** No capability library, no version-aware capability records, no enablement interviewer, and nothing in Transform that executes against packaged software. Non-repo components can be **named and routed**, not assessed.
5. **Declared-vs-observed corroboration.** Nothing reconciles IaC or CMDB declarations against observed reality, or reports a declared-and-not-observed population.
6. **Mechanical provenance arithmetic and a citation leash.** Tier × freshness confidence, provenance-first arbitration, and "every claim cites or is refused" are instructions to a model here, not guards. A definition can ask for them; nothing verifies them.
7. **Determinism.** The same analysis over the same source can return materially different finding counts between runs, so **portfolio roll-ups must be read categorically, never as a numeric before/after delta.** There is no byte-stable artifact a customer can diff to satisfy themselves the tool is deterministic before trusting it.
8. **A cost-to-close ledger.** The price of closing a named gap, stated as four separate dimensions with explicit before/after and an explicit unknown instead of an inferred zero, does not exist. Execution-plan estimates are coarser and composite — and they are **not** a readiness increase.
9. **A coverage and freshness ledger across the whole estate**, including the parts with no repository. The answer to "what do we not know, and when did we last look", as data.
10. **Customer-local execution with no data egress.** Continuous modernization runs analysis and remediation in the customer's own account on their credentials, which is as close as the product gets. The other paths run service-side in a workspace. If a customer's constraint is "nothing leaves", say so plainly rather than designing around it.
11. **Structural separation of the two axes.** Here the independence is a prose rule, not an unreachable symbol. **Expect drift and check for it** — any claim that platform work raised an agentic rung is the defect to look for in your own draft.

---

## 5. Advisory roles, if you split the work

If the engagement is large enough to split, four bounded roles work, and the invariant that makes them safe is that **nothing an agent produces is a fact**:

| Role | Reads | Writes |
|---|---|---|
| **mapper** | candidate evidence for one request | nothing — *proposes* entities and current-state relationships, every field dispositioned mapped / deliberately-unused / unresolved |
| **researcher** | public vendor and product identity only — **no estate at all** | provisional vendor-capability proposals plus one enablement *question* |
| **curator** | validated candidates + current accepted state | the accepted picture — **sole writer**, publishes only against a digest of the exact proposed content |
| **planner** | one accepted version, goals, assertions, coverage | candidate scenarios, typed actions, readiness conclusions, cost-to-close |

Deterministic code validates proposals and computes mechanical consequences — adjacency, reachability, cycles, bounded aggregates, topological waves, landing comparison. It explicitly does **not** choose workload identity, dependency meaning or direction, readiness levels, routes, landings, or recommendation prose. The planner authors conclusions; **it may not number waves, calculate totals, or re-derive thresholds.**

Landing options are scored on effort, financial cost, delivery risk, elapsed time and dependency consequence, with a status from `credible` / `dominated` / `deferred` / `rejected` / `evidence_pending`. Keep that status visible — a rejected option with a stated reason is more useful than a shortlist with no losers.
