# Transformation Definition Catalog

What each definition in this repository consumes and produces, how they are invoked, and what blocks what. Read this when you need to assemble a chain rather than run a single analysis.

Baseline: `atx` 3.18.0. **Managed definitions run inside `atx ct` and are never named on the command line.** Custom definitions are invoked by name and must be published to the registry first. The registry is **per-account and not version-controlled** — drafts expire (roughly 30 days) and names can vanish, so re-publish rather than assume, and verify with `atx custom def get -n <name> --td "$(mktemp -d)"` before depending on a name. `publish` also takes a `--category` (`analysis` or `remediation`) that `atx ct` then enforces — see §0.

---

## 0. What you need on disk

The four **managed** definitions need nothing: they are built into `atx ct` and are never named on the command line. The **six custom** definitions (IAD, bridge, EBA, BAO, portfolio BAO, containerize-service) and the bundled scripts and config templates they depend on exist only in this repository, so stages 4–7 of the advisory workflow need two setup steps:

**1. Clone the repository that carries the definitions.** It is public:

```bash
git clone https://github.com/aws-samples/sample-agentic-readiness-analysis-orchestrator.git
cd sample-agentic-readiness-analysis-orchestrator
ls definitions/custom/        # the six names in the table below
```

Copying `advisor/SKILL.md` and `advisor/references/` into a skills directory installs the *advice*; it does not install the definitions, the BPMN analyzer, or the EBA config template. (The IAD scripts are not in that list: they ship *inside* the published definition — the clone is what you publish from.) Every path in this catalog is **relative to the repository root**, and the commands assume you are running from a clone of it.

> **Why a clone at all.** `atx custom def publish` reads the definition from a local directory
> (`--sd`), so somebody has to have the files once, per account. Nothing about the *running*
> of a custom definition needs the clone afterwards — `atx custom def exec -n <name>` resolves
> from the registry. Treat the clone as the publish-time dependency it is, and expect this step
> to get simpler: the definitions are the artefact, and the repository is only today's delivery
> mechanism for them.

**2. Publish each custom definition you intend to use into the account the work runs in.** `atx custom def exec -n <name>` resolves the name from the registry, not from disk, so an unpublished definition fails with "not found" no matter where the files sit.

```bash
name=portfolio-interapp-dependency-analysis

AWS_REGION=us-east-1 atx custom def publish \
  -n "$name" \
  --sd definitions/custom/"$name" \
  --category analysis \
  --description "Inter-application dependency graph and migration waves from per-repo MOD reports"

atx custom def get -n "$name" --td "$(mktemp -d)"     # verify it resolves
```

Repeat per definition, substituting the name and `--sd definitions/custom/<name>`. Five things to know:

- **`--category` is optional to `publish` and enforced by `atx ct`.** `atx custom def exec -n <name>` — how rows 5–9 below are invoked — does not look at the tag. The two `ct` entry points do, and refuse at the point of use a name they list happily: *`Transformation definition "<name>" has no category, so it can't be used for a custom analysis. Publish it with --category analysis to use it here.`* (`is tagged <x>` replaces `has no category` when the wrong tag is set, and there is a mirror-image wording for remediation). So **`--category remediation` is mandatory for `containerize-service`**, which runs through `atx ct remediation create`. Tag the other five **`--category analysis`** as a matter of course: it costs nothing at publish time and is exactly what `atx ct analysis run --type custom --transformation-name <name>` demands the first time anyone drives one from `ct`.
- **The registry is per-account, so this is per-account setup, not a one-time step.** A definition published in one account does not resolve in another, and `atx custom def get` is the only honest check. It is also not version-controlled: `save-draft` entries expire (roughly 30 days) and names can vanish — re-publish rather than assume.
- **`publish` validates `--sd` against the schema's allowlist and hard-fails on anything else** (`Unsupported file(s) or directory in … transformation definition`). The schema is chosen by which required file is present, and only the directory's **top-level** entries are checked:
  - **SKILL** — `SKILL.md` required, plus optional `workflow.yaml`, `references/`, `scripts/`, `summaries.md`.
  - **LEGACY** — `transformation_definition.md` required, plus optional `summaries.md`, `document_references/`, `references/`. (`LEGACY` is the name the rejection message uses.)

  **Five of the six publish directly from `definitions/custom/<name>`** — IAD included: its `scripts/` and `summaries.md` are both on the SKILL allowlist, and its own `SKILL.md` runs `python3 -I scripts/prepare_corpus.py`, so a staged copy that dropped `scripts/` would publish a definition calling files it does not carry. Only `containerize-service` needs a staged copy, because its contributor `README.md` is not on the LEGACY allowlist:

  ```bash
  stage=$(mktemp -d)
  cp definitions/custom/containerize-service/{transformation_definition.md,summaries.md} "$stage"/
  AWS_REGION=us-east-1 atx custom def publish -n containerize-service --sd "$stage" \
    --category remediation --description "..."
  ```
- `AWS_REGION=us-east-1` is not optional. `atx custom def` does not read the Region from AWS config the way `atx ct` does, and a stray Region surfaces as a DNS failure rather than a clean "not available".
- `atx custom def get` **writes the fetched definition files out** — into the current directory unless you pass `--td <dir>`. Point it at a scratch directory.

`containerize-service` carries two requirements of its own: **`--category remediation`**, and publication **in the auth mode the remediation worker reads** — a pass in the other mode proves nothing. See §A.10.

---

## A. The ten definitions

| # | Definition | Kind | Invocation |
|---|---|---|---|
| 1 | `agentic-readiness-analysis` (ARA, per-repo) | managed | `atx ct analysis run --type agentic-readiness --source <src>` |
| 2 | `modernization-readiness-analysis` (MOD/MODA, per-repo) | managed | `atx ct analysis run --type modernization-readiness --source <src>` |
| 3 | `portfolio-agentic-readiness-analysis` | managed | second phase of the same `--type agentic-readiness` run — **no separate command** |
| 4 | `portfolio-modernization-readiness-analysis` | managed | second phase of `--type modernization-readiness` |
| 5 | `portfolio-interapp-dependency-analysis` (IAD) | custom | `atx custom def exec -n portfolio-interapp-dependency-analysis -p <portfolio-root> -x -t` (runs its own bundled scripts) |
| 6 | `bridge-analysis` | custom | `atx custom def exec -n bridge-analysis -p . -g file://bridge-config.yaml -x -t` |
| 7 | `eba-execution-plan-generator` | custom | `atx custom def exec -n eba-execution-plan-generator -p . -g file://atx-config-exec-plan.yaml -x -t` |
| 8 | `bpmn-opportunity-analysis` (BAO, per-repo) | custom | run the analyzer, then `atx custom def exec -n bpmn-opportunity-analysis -p . -g file://bao-config.yaml -x -t` |
| 9 | `portfolio-bpmn-opportunity-analysis` | custom | `atx custom def exec -n portfolio-bpmn-opportunity-analysis -p . -x -t` (auto-discovers, no config) |
| 10 | `containerize-service` | custom (remediation) | `atx ct remediation create --repo <src>::<repo> --source <src> --transformation-name containerize-service --local` |

> **The two configs you must author by hand.** Neither has a shipped template.
> `bridge-config.yaml` — wants the **Markdown** portfolio reports, not the JSON:
> ```yaml
> additionalPlanContext: |
>   portfolio_name: "my-platform"
>   portfolio_ara_report_path: "<abs path to *-portfolio-ara-report.md>"
>   portfolio_mod_report_path: "<abs path to *-portfolio-mod-report.md>"
> ```
> `bao-config.yaml` — one required field, the analyzer's JSON output:
> ```yaml
> additionalPlanContext: |
>   analysis_report_path: "<abs path to the run_analysis.py JSON>"
> ```

**Two different path bases, and mixing them is the commonest setup failure.** `-p` and the `-g file://` config are read relative to the **portfolio root** — the directory holding the per-repo reports, which is where `.` points in rows 6–9. Script and `--sd` paths are relative to the **repository root**. They are rarely the same directory, so give the script its full repo-rooted path.

### 1. `agentic-readiness-analysis` — per-repo ARA

**Consumes** repository source code. A full static scan: IaC, application source, API specifications (OpenAPI, AsyncAPI, GraphQL, Smithy), CI/CD, containers, dependency manifests, configuration. Optional `additionalPlanContext`: `repo_type`, `agent_scope`, `service_archetype`, `context`, `priority`, `tags` — **all infer-else-honor; absence never lowers a score.**

**Produces** four artifacts `{repo}-ara-report.{md,json,html,metadata.json}`. **43 questions / 8 sections** (API 8, AUTH 7, STATE 7, HITL 3, DATA 7, DISC 3, OBS 3, ENG 5). A readiness profile in `classification.tier`, `findings[]` + `evaluations[]`, and `ara_metadata.native_severity`.

**Requires** a readable repository and write permission for the bundle. Read-only against the code; stays on the current branch.

### 2. `modernization-readiness-analysis` — per-repo MOD

**Consumes** repository source code. The same scan plus Kubernetes / Helm / Kustomize / ArgoCD / Flux, database artifacts (engines, migrations, stored procedures, ORM), analytics and streaming, and AI/agent frameworks. Optional context: `repo_type`, `context`, `priority`, `tags`, `preferences{prefer,avoid}`, `service_archetype`. **Explicitly ignores `agent_scope`.**

**Produces** four artifacts `{repo}-mod-report.*`. **37 questions / 5 categories** (INF 11, APP 6, DATA 4, SEC 7, OPS 9) scored 1–4; `overall_score` = mean of the five equally-weighted category means; `pathways[]` with all 7 pathways each marked Triggered / Not Triggered / Not Applicable; and a conditional Decomposition Strategy when `APP-Q2 < 3`.

### 3. `portfolio-agentic-readiness-analysis`

**Consumes ≥ 2 per-repo `*-ara-report.json`** (JSON only). Reads `classification.{tier,blocker_count,risk_safety_count,...}`, `findings[].{question_id,severity,ara_metadata.native_severity,description,gap,recommendation,evidence,safety_impact}`, `evaluations[]`, and `metadata.{repo_name,repo_type,agent_scope,analysis_date}`. Optional context: `portfolio_name`, `context`, `service_inventory[]`, `dependency_overrides[]`.

**Produces** four artifacts `{portfolio}-portfolio-ara-report.*`: executive dashboard and readiness distribution, blocker heatmap by section, readiness snapshot, cross-cutting BLOCKERs (present in ≥ 2 repos), cross-cutting RISKs (threshold `max(3, 33% of applicable repos)`, floor 2 under four repos), dependency map, remediation guidance, **program recommendations**, `PORT-ARA-Q1…Q5`, and a service-by-service summary.

**Requires ≥ 2 valid ARA report JSONs or it terminates.** Discovery **must follow symlinks** (`find -L`, or `os.walk(followlinks=True)`) — per-repo outputs are symlinked under mangled names, and a bare recursive search finds zero.

### 4. `portfolio-modernization-readiness-analysis`

**Consumes ≥ 2 per-repo `*-mod-report.json`.** Reads `overall_score`, `categories[]`, `pathways[]`, `findings[]`, `metadata`. Optional context: `portfolio_name`, `context`, `preferences`, `service_inventory[]` (including per-service `service_archetype` passthrough), `dependency_overrides[]`. Ignores `agent_scope`.

**Produces** four artifacts `{portfolio}-portfolio-mod-report.*`: score overview and category averages, tech-stack summary and blueprint candidates, dependency graph (coupling, fan-in/out, blast radius, cycles, critical path), two-tier cross-cutting concerns (Foundational Blockers below 2 in 2+ repos; Improvement Opportunities below 3 at threshold), infrastructure cross-referencing, **four fixed roadmap phases** (Cross-Cutting Foundation months 0–1, Quick Wins 1–2, Foundation 2–4, Advanced 4–6+), pathway aggregation, integration opportunities, risk matrix, resource allocation, **AWS programs**, `PORT-MOD-Q1…Q5`, and a target-state architecture.

Same symlink rule. **`tier_distribution` must be counted verbatim from per-repo `classification.tier`, never re-derived from score bands.**

### 5. `portfolio-interapp-dependency-analysis` — IAD

**This one both assesses and plans, which is why it is not simply "the graph stage".** It
produces the relationship *assessment* — who depends on whom through what mechanism, coupling
scores, fan-in/fan-out, blast radius, foundation services, circular dependencies, and how much
of the estate has no integration evidence at all — and the *plan* that those constraints force:
the migration wave order, plus a `critical_path_length` that is a topology floor no amount of
staffing reduces. Do not re-derive either half by reading reports yourself; run the definition
and interpret what it emits.

**Consumes per-repo MOD artifacts only — no source scan.** From the JSON: `findings[].{description,gap,recommendation,evidence.file}`, `top_gaps[]`, `decomposition_strategy.effort_factors`, `metadata.archetype_justification`. **Plus the per-repo `.md`**, where `#### {QID}` Finding / Gap / Evidence rows on high-yield questions name peers that exist nowhere else. Optional context: `portfolio_name`, `context`, `dependency_overrides[]`, `service_aliases{}`, `external_systems[]`, `critical_services[]`.

**Produces** four artifacts under `interapp-dependency-analysis/`: a typed directed graph (`sync` / `async` / `shared_db` / `shared_infra`), coupling scores, fan-in/out, blast radius, Foundation / Hub / Leaf / Isolated classes, Tarjan SCCs run twice (app-only and with resources), critical path, shared-resource clusters, per-service coverage (`Good` / `Partial` / `None` / `Silent`), **migration waves** (Wave 0 → topological → Wave ∞), and a closable-gap list.

**Requires ≥ 2 per-repo `*-mod-report.json` beneath the root** (the per-repo `.md` is optional and its absence only degrades enrichment). **The definition runs its own bundled scripts (`scripts/prepare_corpus.py` for steps 1–3, `scripts/render_report.py` for 5–9) — never write a replacement, and never stage the corpus by hand.** The signal→edge classification step is the agent's own work, one batch at a time, appended after each batch — never delegated to a research-only subagent.

### 6. `bridge-analysis`

**Consumes both portfolio reports as Markdown** — `portfolio_ara_report_path` and `portfolio_mod_report_path`, plus `portfolio_name`. **All three are required with no derivation.** Optional `portfolio_bao_report_path` enables section 6.

**Produces** a single `{portfolio_name}-bridge-report.md` at the portfolio root: §1 shared-remediation mapping, §2 the **agentic-readiness delta** ("X of Y ARA BLOCKERs resolved by MOD Phase 0"), §3 a MOD readiness gate (advisory when the SEC or OPS average is below 2.0), §4 a unified remediation sequence with dual-resolution items, §5 shared-findings deduplication, §6 a BAO + ARA readiness matrix (conditional).

**The only genuine AND-gate in the chain:** both portfolio reports must exist and be readable or it terminates. It wants **Markdown, not JSON** — a JSON-only run has nothing to read. Failure is non-destructive: the ARA and MOD reports are untouched.

### 7. `eba-execution-plan-generator`

**Consumes ≥ 1 portfolio report JSON** (ARA and/or MOD; supplying both enables cross-dimension dependency detection). Per-service reports are optional enrichment. **This is the only definition that genuinely needs human planning context**: `team_size`, `timeline_constraint`, `budget_constraint`, `compliance_requirements[]`, `availability_requirement`, `risk_tolerance`, `existing_capabilities`, `priority_pathways` / `excluded_pathways`, `preferences`, `ai_acceleration` (+ overrides), `service_inventory[]`, `dependency_overrides[]`.

**Produces** four artifacts `{portfolio}-portfolio-exec-plan.*`: deduplicated work streams (one per triggered pathway; one per ARA category with BLOCKERs becoming mandatory tasks and RISKs recommended), cross-dimension dependencies, shared-infrastructure tasks, a phased timeline with parallelization, a risk register, three-point effort and cost, and decision points.

⚠️ **Path trap.** Its documented input names are `{portfolio-name}-mod-portfolio-report.json` / `-ara-portfolio-report.json`, but the portfolio definitions **emit** `{portfolio_name}-portfolio-mod-report.json` / `-portfolio-ara-report.json`. **Resolve real paths from the analysis record and pass them explicitly; never rely on either literal.**

### 8. `bpmn-opportunity-analysis` — BAO, per-repo

**Consumes neither source nor reports** — it reads the deterministic JSON emitted by the bundled BPMN analyzer (`tools/bpmn-analyzer/run_analysis.py` in the clone) at `analysis_report_path` (required): `process`, `constraints`, `tasks[]` (ai_benefit / complexity / risk / effort / composite, `migration_type`, `cost_estimate`), `summary`, `dependencies`. Optional `context`, `daily_volume` (default 100), `priority`, `tags`. **`ara_report_path` is deprecated and ignored** — ARA cross-referencing belongs to `bridge-analysis`.

**Produces** `{process}-bpmn-opportunity-report.md`: per-task opportunity category (Automate / Data Platform / Agent build-now / Agent data-first / Human Required), autonomy level (Autonomous / Prepared / Exploration / Guardrail, capped at Prepared on regulatory signals), model-cost projection, a prioritized roadmap, and dependency listing.

**Requires** a BPMN 2.0 model (`.bpmn`, `.bpmn2`, `.bpmn20.xml`) **and** the analyzer JSON. **Scores and `migration_type` are deterministic — do not override them.**

### 9. `portfolio-bpmn-opportunity-analysis`

**Consumes** per-repo `*-bpmn-opportunity-report.md` files. **Requires ≥ 1** (not 2).

**Produces** `bpmn-opportunity-analysis/{portfolio}-portfolio-bao-report.md`: portfolio opportunity summary, cross-repo patterns, dependency coverage, model-consumption forecast, and Waves 1–3, where Wave 3 "system remediation" is deliberately left for `bridge-analysis` to populate. Explicitly does **not** touch ARA or MOD.

### 10. `containerize-service`

**Consumes** a repository, with the MOD `INF-Q1` finding as its reason to exist.

**Produces** only `Dockerfile`, `.dockerignore`, `k8s/deployment.yaml`, `k8s/service.yaml`, plus a PR/branch (or a local branch) documenting the detected runtime, assumptions, and follow-up hardening.

**Requires** publication to the registry with **`--category remediation`** and **in the auth mode the remediation worker reads** — a wrong category is refused outright (*"it can't be used for remediation"*), and a pass in the other auth mode proves nothing. The worktree must be clean for the `ct remediation` path, and a just-analyzed repository is dirty because `ct` writes reports into the tree. Fallback: `atx custom def exec -n containerize-service -p <abs-repo-path> -x -t`. It is also the one definition on the **LEGACY** schema (`transformation_definition.md`, plus optional `summaries.md` / `document_references/` / `references/`) rather than the SKILL schema the other five use — and so the one that needs a staged copy to publish, because its contributor `README.md` is not on that allowlist (§0).

---

## B. Ordering — what blocks what

```
            ┌─ atx ct source add → discovery scan ─┐
            ▼                                      ▼
[1] ARA per-repo ──auto──► [3] Portfolio ARA        [2] MOD per-repo ──auto──► [4] Portfolio MOD
      (needs source)         (needs ≥2 ARA JSON)      (needs source)             (needs ≥2 MOD JSON)
            │                      │                       │                          │
            │                      │                       └──────► [5] IAD (MOD JSON + MD; ≥2)
            │                      │                                          │
            │                      └──────────┬────────────────────────────────┘
            │                                 ▼
            └───────────────────────► [6] bridge-analysis  (needs BOTH portfolio MD reports)
                                              │
            [8] BAO per-repo → [9] Portfolio BAO ──(optional §6 input)──┘
                                              │
                                              ▼
                                   [7] EBA execution plan  (≥1 portfolio JSON + human constraints)
                                              │
                                              ▼
                                   [10] remediation (per repo, per finding)
```

Stated plainly:

1. **Discovery before any managed analysis.** No discovered repositories means nothing runs.
2. **Per-repo before portfolio, always** — and **the portfolio phase is not a separate command**; it is phase 2 of the same `analysis run`. It silently produces nothing below two repository reports.
3. **Do not run the two managed analyses concurrently.** They run in-process and conflict on git state; the same applies to a `custom def exec` racing an `analysis run`. Sequence them; the order between ARA and MOD is otherwise free because they are independent.
4. **IAD runs after per-repo MOD and does not need portfolio MOD** (it only uses it to derive a name). It can start before the portfolio MOD phase finishes.
5. **`bridge-analysis` is the only genuine AND-gate**, and it wants Markdown.
6. **EBA last among planners.** It is an OR-gate (≥ 1 portfolio report), so it degrades to a single-axis plan; feed it both for cross-dimension detection.
7. **Remediation after findings, and after the worktree is clean.**

---

## C. Steering reaches managed definitions only through flags

`atx ct analysis run` **rejects `-g`/`--configuration` for the built-in types.** Managed-definition steering reaches `additionalPlanContext` only through flags — ARA: `--context`, `--agent-scope`; MOD: `--context`, `--prefer`, `--avoid`. Of these **only ARA `--agent-scope` moves scores**; the rest bias framing and recommendations and must never change eligibility, trigger, score, tier, or status. There is **no `--agent-type`**.

**Omitting `--agent-scope` does not mean read-only.** ARA infers scope from the repository's write surface, so the five conditional BLOCKERs (`API-Q4`, `STATE-Q1`, `AUTH-Q6`, `DATA-Q1`, `DATA-Q2`) stay live on a genuinely write-capable target. Absence never lowers a score.

`-g` **is** required for the custom definitions that take real inputs — bridge, EBA, BAO.

---

## D. Where the program library sits

`references/program-library.md` inside each portfolio definition: the AWS program and go-to-market catalog (MAP, OLA, AppMod, EBA, SHIP, AI DLC, AXE, Innovation EBA, FORGE and more) with per-program signal patterns, "do not recommend when" exclusions, qualification criteria, and a reasoning checklist.

- **Portfolio definitions only.** Portfolio ARA evaluates every `[ARA]` / `[ARA+MOD]` program including the `[ARA-anchor]` set; portfolio MOD evaluates every `[MOD]` / `[ARA+MOD]` program. **Per-repo definitions never recommend a program** — they lack the cross-repo and customer-segment context to qualify one. Portfolio MOD states this as a hard rule: the section appears only in portfolio reports.
- **Selection discipline:** include only if signals match **and** no exclusion fires; group `Funded Programs → Engagement Models`; apply the assessment-overlap and engagement-model rules; **cap at 3–5**; never expose the internal 1–4 maturity score — use severity and classification language only.
- **ARA-side sequencing is prescribed:** AI DLC → AXE → Innovation EBA (which can run in parallel with AXE if the use cases are independent) → FORGE, which feeds AXE's data-architecture phase.
- **The file is intentionally duplicated** in both portfolio definition folders, because each folder is a self-contained publishable package with no cross-package reference at runtime. Edit one, edit both, and `diff` them before publishing or one copy ships stale.

---

## E. Recommended end-to-end sequence

```
0  Prereqs      aws sts get-caller-identity; export AWS_REGION=us-east-1
                atx ct status --health          # never `atx ct server` — deprecated, blocks the shell
                clone this repository, then per custom definition you will use (§0):
                atx custom def publish -n <name> --sd definitions/custom/<name> \
                  --category analysis --description "..."   # containerize-service: --category remediation
                atx custom def get -n <name> --td "$(mktemp -d)"   # verify; per-account, repeat per account
1  Source       atx ct source add --name <src> --provider local --path <abs parent dir>
2  Discover     atx ct discovery scan --source <src>          # each repo needs a .git dir
3  ARA          atx ct analysis run --type agentic-readiness --source <src> [--context "..."] [--agent-scope ...]
                → per-repo ARA bundles + portfolio ARA (auto, needs ≥2 repos)
4  MOD          atx ct analysis run --type modernization-readiness --source <src> [--context "..."] [--prefer ...] [--avoid ...]
                → per-repo MOD bundles + portfolio MOD (auto, needs ≥2 repos)
                ‼ not concurrent with step 3
5  Locate       atx ct analysis get --id <id> --json   → read report_paths; do NOT guess filenames
6  IAD          atx custom def exec -n portfolio-interapp-dependency-analysis -p <portfolio-root> -x -t
                → classify signal batches one at a time, append after each, then render
7  Bridge       atx custom def exec -n bridge-analysis -p . -g file://bridge-config.yaml -x -t
                → the modernization dividend + unified sequence + dedup   ← the ARA/MOD weave
8  (BPMN track, only if process models exist — independent of 3–7)
   8a  python3 tools/bpmn-analyzer/run_analysis.py …   → deterministic JSON
   8b  atx custom def exec -n bpmn-opportunity-analysis -p . -g file://bao-config.yaml -x -t
   8c  atx custom def exec -n portfolio-bpmn-opportunity-analysis -p . -x -t
   8d  re-run step 7 with portfolio_bao_report_path → bridge §6 readiness matrix
9  EBA          atx custom def exec -n eba-execution-plan-generator -p . -g file://atx-config-exec-plan.yaml -x -t
                → needs team_size + timeline; feed BOTH portfolio reports for cross-dimension detection
10 Remediate    atx ct remediation create --repo <src>::<repo> --source <src> \
                  --transformation-name containerize-service --local
                → needs --category remediation at publish time, or ct refuses the name
                → commit or clean the worktree first; verify the name resolves in the worker's auth mode
```

**Minimum viable advisory path: 2 → 3 → 4 → 7** — both axes, bridged. Add **6** the moment the estate has more than a handful of applications; without it the roadmap phases are calendar buckets. Add **9** only when the customer supplies planning constraints, because it cannot infer team size or timeline from code.
