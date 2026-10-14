#!/usr/bin/env python3
"""Steps 5-9 helper: graph math, clustering, waves, and the four-artifact bundle.

Takes the agent's classified edges and turns them into the full report. Every
computation in SKILL.md Steps 5-8 lives here so it is deterministic and
identical on every run; the agent supplies judgment (which edges exist), this
supplies arithmetic (what they imply).

Inputs
  <portfolio-root>/.iad-work/corpus.json   written by prepare_corpus.py
  <portfolio-root>/.iad-work/edges.json    written by the agent, schema below

edges.json:
  {
    "portfolio_name": "anycompany",                     # optional
    "portfolio_name_source": "supplied",          # optional
    "context": "free text",                       # optional
    "extra_nodes": [                              # external systems + resources
      {"name": "AnyCompanyLedgerDb", "kind": "resource",
       "resource_kind": "database", "platform": null}
    ],
    "edges": [
      {"source": "<slug|name>", "target": "<slug|name>",
       "type": "sync|async|shared_db|shared_infra", "protocol": "HTTP",
       "provenance": "declared|inferred_named|inferred_shared_resource",
       "confidence": "high|medium|low", "direction_confidence": "high",
       "matched_via": "exact_key", "md_enriched": true,
       "evidence": [{"repo": "...", "question_id": "INF-Q4",
                     "source_artifact": "md", "raw_text": "..."}]}
    ],
    "unresolved_signals": [
      {"source_repo": "...", "question_id": "...", "candidate_names": [],
       "resolved_target": null, "reason": "no_alias_match", "raw_text": "..."}
    ],
    "closable_gaps": [
      {"gap": "...", "blocked_signals": 12, "recommended_entry": "..."}
    ]
  }

Usage:  python3 -I render_report.py <portfolio-root>
Stdlib only. Python 3.8+.
"""
import sys, os, re, json, html, collections, datetime

EDGE_TYPES = ("sync", "async", "shared_db", "shared_infra")
TD_VERSION = "portfolio-interapp-dependency-1.0.0"
OVERSIZE_FRACTION = 0.40     # 02-graph-metrics.md 5.1


# --------------------------------------------------------------- utilities
def nid(name):
    s = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    return s or "unnamed"


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def cell(x, limit=160):
    """Markdown-table-safe cell: escape pipes, collapse newlines, truncate."""
    s = re.sub(r"\s+", " ", "" if x is None else str(x)).strip()
    s = s.replace("|", "\\|")
    return (s[: limit - 1] + "…") if len(s) > limit else s


def pct(n, d):
    return round(100.0 * n / d, 1) if d else 0.0


# ------------------------------------------------------------- graph build
def build_nodes(corpus, spec):
    nodes, by_key, slug_to_id, ambiguous = {}, {}, {}, set()

    for s in corpus["services"]:
        # Report slugs are NOT unique across a portfolio -- several repos can emit
        # e.g. 'src-mod-report.json'. Disambiguate with the repo directory so two
        # distinct services never collapse into one node.
        i = nid(s["slug"])
        if i in nodes:
            i = nid(f"{s['repo_dir']}-{s['slug']}")
        nodes[i] = {
            "id": i, "name": s["repo_name"], "kind": "internal",
            "resource_kind": None, "platform": None,
            "repo_dir": s["repo_dir"], "report_slug": s["slug"],
            "per_repo_json_path": s["json_path"],
            "per_repo_md_path": s["md_path"], "md_available": s["md_available"],
            "overall_score": s["overall_score"], "tier": s["tier"],
            "service_archetype": s["service_archetype"],
            "repo_type": s["repo_type"],
            "repository_priority": s["repository_priority"],
            "aliases": s["aliases"],
            "match_keys": {"exact": [], "stripped": []},
        }
        slug_to_id[s["slug"]] = i
        for a in [s["slug"], s["repo_name"], s["repo_dir"]] + list(s["aliases"]):
            for k in (nid(a), re.sub(r"[^a-z0-9]", "", str(a).lower())):
                if not k:
                    continue
                if k in by_key and by_key[k] != i:
                    ambiguous.add(k)      # never auto-resolve a colliding key
                else:
                    by_key[k] = i
    for k in ambiguous:
        by_key.pop(k, None)

    for e in spec.get("extra_nodes") or []:
        i = nid(e.get("name"))
        if i in nodes:
            continue
        kind = e.get("kind") or "external"
        nodes[i] = {
            "id": i, "name": e.get("name"), "kind": kind,
            "resource_kind": e.get("resource_kind") if kind == "resource" else None,
            "platform": e.get("platform"),
            "repo_dir": None, "report_slug": None,
            "per_repo_json_path": None, "per_repo_md_path": None,
            "md_available": False, "overall_score": None, "tier": None,
            "service_archetype": None, "repo_type": None,
            "repository_priority": None, "aliases": [],
            "match_keys": {"exact": [], "stripped": []},
        }
        by_key[i] = i
        by_key[re.sub(r"[^a-z0-9]", "", str(e.get('name', '')).lower())] = i
    return nodes, by_key, slug_to_id


def resolve(ref, nodes, by_key):
    i = nid(ref)
    if i in nodes:
        return i
    return by_key.get(i) or by_key.get(re.sub(r"[^a-z0-9]", "", str(ref).lower()))


def build_edges(spec, nodes, by_key):
    merged, dangling, malformed = {}, [], []
    for n, e in enumerate(spec.get("edges") or []):
        s = resolve(e.get("source"), nodes, by_key)
        t = resolve(e.get("target"), nodes, by_key)
        # Accept "edge" as an alias for "type": it is the natural key name and
        # agents reach for it. Tolerate the synonym, reject anything unusable.
        ty = e.get("type") or e.get("edge") or e.get("edge_type")
        if not s or not t:
            dangling.append({"index": n, "source": e.get("source"),
                             "target": e.get("target"),
                             "reason": "endpoint does not resolve to a node"})
            continue
        if ty not in EDGE_TYPES:
            # NEVER skip silently. A dropped edge is invisible data loss that
            # surfaces as an empty graph with no error -- the exact failure this
            # analysis exists to correct.
            malformed.append({"index": n, "source": e.get("source"),
                              "target": e.get("target"), "type_found": ty,
                              "keys_present": sorted(e.keys())})
            continue
        if s == t:
            continue
        k = (s, t, ty)
        if k not in merged:
            merged[k] = {
                "source": s, "target": t, "type": ty,
                "protocol": e.get("protocol"),
                "provenance": e.get("provenance") or "inferred_named",
                "confidence": e.get("confidence") or "medium",
                "direction_confidence": e.get("direction_confidence") or "medium",
                "matched_via": e.get("matched_via"),
                "md_enriched": bool(e.get("md_enriched")),
                "derived_from_cluster": e.get("derived_from_cluster"),
                "evidence": list(e.get("evidence") or []),
                "occurrence_count": 1,
            }
        else:
            m = merged[k]
            m["evidence"].extend(e.get("evidence") or [])
            m["occurrence_count"] += 1
            m["md_enriched"] = m["md_enriched"] or bool(e.get("md_enriched"))
            prov_rank = {"declared": 0, "inferred_named": 1,
                         "inferred_shared_resource": 2}
            if prov_rank.get(e.get("provenance"), 3) < prov_rank.get(m["provenance"], 3):
                m["provenance"] = e.get("provenance")
            # confidence = weakest link; never promote on repetition
            cr = {"high": 0, "medium": 1, "low": 2}
            if cr.get(e.get("confidence"), 1) > cr.get(m["confidence"], 1):
                m["confidence"] = e.get("confidence")
    for m in merged.values():
        if m["provenance"] == "declared":
            m["confidence"] = "high"
    return list(merged.values()), dangling, malformed


def coupling(edges):
    """5.1 per ordered pair."""
    types = collections.defaultdict(set)
    for e in edges:
        types[(e["source"], e["target"])].add(e["type"])
    out = {}
    for pair, ts in types.items():
        if ("sync" in ts and "shared_db" in ts) or len(ts) >= 3:
            out[pair] = "High"
        elif "sync" in ts or len(ts) == 2:
            out[pair] = "Medium"
        else:
            out[pair] = "Low"
    for e in edges:
        e["coupling"] = out[(e["source"], e["target"])]
    return out


def tarjan(nodes, adj):
    idx, low, on, st, out, ctr = {}, {}, set(), [], [], [0]
    sys.setrecursionlimit(10000)

    def visit(v):
        idx[v] = low[v] = ctr[0]; ctr[0] += 1
        st.append(v); on.add(v)
        for w in adj.get(v, ()):
            if w not in idx:
                visit(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                out.append(sorted(comp))
    for v in nodes:
        if v not in idx:
            visit(v)
    return out


def metrics(edges, nodes, observed=None):
    """5.2 fan-in/out, blast radius (inbound traversal), classification.

    `edges` is observed + derived and drives blast radius, which should account
    for coupling through shared resources. `observed` (defaulting to `edges`)
    drives Foundation/Hub/Leaf classification, which must NOT: an N-member
    database cluster hands every member N-1 derived edges, so classifying on the
    combined degree makes most of a legacy portfolio look like a hub and renders
    the label useless."""
    if observed is None:
        observed = edges
    internal = {i for i, n in nodes.items() if n["kind"] == "internal"}
    fi, fo = collections.Counter(), collections.Counter()
    fid, fod = collections.Counter(), collections.Counter()
    inbound = collections.defaultdict(set)
    for e in edges:
        inbound[e["target"]].add(e["source"])
        if e["provenance"] == "inferred_shared_resource":
            fod[e["source"]] += 1; fid[e["target"]] += 1
    for e in observed:
        fo[e["source"]] += 1; fi[e["target"]] += 1

    def blast(n):
        seen, q, via = set(), [n], False
        while q:
            cur = q.pop()
            for dep in inbound.get(cur, ()):
                if dep not in seen:
                    seen.add(dep); q.append(dep)
                    if nodes.get(dep, {}).get("kind") != "internal":
                        via = True
        seen.discard(n)
        return len(seen & internal), via

    cp = coupling(observed)
    per = []
    for i in sorted(nodes):
        b, via = blast(i)
        a, b_ = fi[i], fo[i]
        if a >= 3 and b_ >= 3:
            cls = "Hub"
        elif a >= 3 and b_ <= 1:
            cls = "Foundation"
        elif a <= 1 and b_ >= 2:
            cls = "Leaf"
        elif a == 0 and b_ == 0:
            cls = "Isolated"
        else:
            cls = "none"
        per.append({
            "id": i, "fan_in": a, "fan_out": b_,
            "fan_in_derived": fid[i], "fan_out_derived": fod[i],
            "blast_radius_count": b,
            "blast_radius_percent": pct(b, len(internal)),
            "traverses_resource": via, "class": cls,
            "coupling_pairs": [
                {"peer": nodes[p[0]]["name"], "coupling": c, "direction": "inbound"}
                for p, c in cp.items() if p[1] == i
            ][:12],
        })
    return per, internal


def clusters_and_derived(edges, nodes, internal_n):
    """Step 6 clustering + derived pairs, with the 5.1 oversize guard."""
    members = collections.defaultdict(set)
    for e in edges:
        if nodes[e["target"]]["kind"] == "resource":
            members[e["target"]].add(e["source"])

    out, derived, dropped = [], [], []
    for res, mem in members.items():
        mem = {m for m in mem if nodes[m]["kind"] == "internal"}
        if len(mem) < 2:
            continue
        if internal_n and len(mem) > OVERSIZE_FRACTION * internal_n:
            dropped.append({"resource": nodes[res]["name"], "members": len(mem),
                            "reason": "generic_resource_name: cluster exceeds "
                                      f"{int(OVERSIZE_FRACTION*100)}% of portfolio"})
            continue
        risk = ("High" if len(mem) >= 5 else "Medium" if len(mem) >= 3 else "Low")
        kind = nodes[res]["resource_kind"] or "other"
        out.append({
            "resource": nodes[res]["name"], "resource_id": res,
            "resource_kind": kind, "member_count": len(mem),
            "member_services": sorted(nodes[m]["name"] for m in mem),
            "coordination_risk": risk, "oversized": False,
        })
        ty = "shared_db" if kind == "database" else "shared_infra"
        ms = sorted(mem)
        for a in ms:
            for b in ms:
                if a != b:
                    derived.append({
                        "source": a, "target": b, "type": ty,
                        "provenance": "inferred_shared_resource",
                        "confidence": "medium",
                        "derived_from_cluster": nodes[res]["name"],
                        "evidence": [], "occurrence_count": 1,
                        "coupling": "Low" if ty == "shared_infra" else "Medium",
                    })
    out.sort(key=lambda c: -c["member_count"])
    return out, derived, dropped


def waves(edges, nodes, per, cycles_app, clusters):
    # `edges` here must be the OBSERVED set. Sequencing on derived pairs puts
    # every member of every shared-resource cluster into Wave 0, which collapses
    # the wave count below the critical path and makes the plan unusable.
    """Step 8 wave assignment + tracks + validation."""
    internal = {i for i, n in nodes.items() if n["kind"] == "internal"}
    m = {p["id"]: p for p in per}
    in_cycle = {n for c in cycles_app for n in c}
    # High-risk shared resources become explicit decoupling work items (reported
    # in the Shared Resource Clusters section); their member services are NOT all
    # forced into Wave 0, which would be most of a legacy portfolio.
    w0 = {i for i in internal
          if m[i]["class"] in ("Foundation", "Hub") or i in in_cycle}

    deps = collections.defaultdict(set)
    for e in edges:
        if e["source"] in internal and e["target"] in internal:
            deps[e["source"]].add(e["target"])

    prio = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, None: 4}
    rest, assigned, waves_out = internal - w0, dict.fromkeys(w0, 0), []
    cur = 1
    while rest:
        ready = {i for i in rest if not (deps[i] & rest)}
        if not ready:
            break
        for i in ready:
            assigned[i] = cur
        rest -= ready
        cur += 1
    unseq = sorted(rest)

    for w in range(0, cur):
        mem = sorted([i for i, v in assigned.items() if v == w],
                     key=lambda i: (prio.get(nodes[i]["repository_priority"], 4),
                                    -m[i]["blast_radius_count"],
                                    -(nodes[i]["overall_score"] or 0)))
        if not mem and w:
            continue
        # tracks: connected components within the wave
        ms, seen, tracks = set(mem), set(), []
        und = collections.defaultdict(set)
        for e in edges:
            if e["source"] in ms and e["target"] in ms:
                und[e["source"]].add(e["target"])
                und[e["target"]].add(e["source"])
        for i in mem:
            if i in seen:
                continue
            comp, q = [], [i]
            while q:
                c = q.pop()
                if c in seen:
                    continue
                seen.add(c); comp.append(c)
                q.extend(und[c] - seen)
            tracks.append(sorted(nodes[c]["name"] for c in comp))
        waves_out.append({
            "wave": w,
            "name": ("Foundation and Blockers" if w == 0 else f"Wave {w}"),
            "services": [
                {"service": nodes[i]["name"],
                 "priority": nodes[i]["repository_priority"],
                 "blast_radius": m[i]["blast_radius_count"],
                 "class": m[i]["class"],
                 "reason": ("foundation/hub" if m[i]["class"] in ("Foundation", "Hub")
                            else "in cycle" if i in in_cycle
                            else "dependencies satisfied")}
                for i in mem],
            "service_count": len(mem),
            "parallel_tracks": [{"track": f"Track {n+1}", "services": t,
                                 "count": len(t)}
                                for n, t in enumerate(tracks)],
        })
    if unseq:
        waves_out.append({
            "wave": None, "name": "Unsequenceable",
            "services": [{"service": nodes[i]["name"], "priority":
                          nodes[i]["repository_priority"], "blast_radius":
                          m[i]["blast_radius_count"], "class": m[i]["class"],
                          "reason": "remaining dependencies form a cycle"}
                         for i in unseq],
            "service_count": len(unseq), "parallel_tracks": [],
        })
    return waves_out, assigned, unseq, w0


def critical_path(edges, nodes, cycles):
    internal = {i for i, n in nodes.items() if n["kind"] == "internal"}
    comp = {}
    for n, c in enumerate(cycles):
        for x in c:
            comp[x] = f"scc{n}"
    rep = {i: comp.get(i, i) for i in internal}
    adj = collections.defaultdict(set)
    for e in edges:
        if e["source"] in internal and e["target"] in internal:
            a, b = rep[e["source"]], rep[e["target"]]
            if a != b:
                adj[a].add(b)
    memo = {}

    def longest(v, stack):
        if v in memo:
            return memo[v]
        if v in stack:
            return []
        best = []
        for w in adj.get(v, ()):
            cand = longest(w, stack | {v})
            if len(cand) > len(best):
                best = cand
        memo[v] = [v] + best
        return memo[v]

    best = []
    for v in set(rep.values()):
        p = longest(v, frozenset())
        if len(p) > len(best):
            best = p
    names = []
    for x in best:
        if x.startswith("scc"):
            n = int(x[3:])
            names.append("cycle{" + ", ".join(nodes[y]["name"] for y in cycles[n]) + "}")
        else:
            names.append(nodes[x]["name"])
    return {"nodes": names, "length": len(names)}


# ------------------------------------------------------------------ mermaid
def mermaid_blocks(d, nodes):
    """Scoped Mermaid diagrams.

    One diagram of the whole graph is unreadable past a few dozen nodes, and a
    legacy portfolio is mostly shared-data coupling anyway. So emit several
    focused views instead of one hairball: the app-to-app call graph, each
    high-risk shared resource with its consumers, and the foundation services
    with their dependents.
    """
    def lbl(n):
        return str(n["name"]).replace('"', "'").replace("\\", "/")[:46]

    def decl(i, n):
        if n["kind"] == "internal":
            return '  %s["%s"]' % (i, lbl(n))
        if n["kind"] == "external":
            return '  %s[/"%s"/]' % (i, lbl(n))
        return '  %s[("%s")]' % (i, lbl(n))

    out = []

    aa = [e for e in d["edges"]
          if nodes[e["source"]]["kind"] == "internal"
          and nodes[e["target"]]["kind"] == "internal"]
    if aa:
        used = {x for e in aa for x in (e["source"], e["target"])}
        L = ["flowchart LR"] + [decl(i, nodes[i]) for i in sorted(used)]
        for e in sorted(aa, key=lambda e: (e["source"], e["target"])):
            arrow = "-.->" if e["confidence"] == "low" else "-->"
            L.append("  %s %s|%s| %s" % (e["source"], arrow, e["type"], e["target"]))
        out.append(("Application-to-Application Call Graph",
                    "%d direct dependencies between %d services. Dashed arrows are "
                    "low confidence." % (len(aa), len(used)),
                    "\n".join(L)))

    for c in d["shared_resource_clusters"]:
        if c["coordination_risk"] != "High":
            continue
        rid = c["resource_id"]
        wanted = set(c["member_services"])
        members = [i for i, n in nodes.items()
                   if n["kind"] == "internal" and n["name"] in wanted]
        if not members:
            continue
        L = ["flowchart LR", decl(rid, nodes[rid])]
        L += [decl(i, nodes[i]) for i in sorted(members)]
        for i in sorted(members):
            L.append("  %s --> %s" % (i, rid))
        L.append("  classDef res fill:#fff4e0,stroke:#8a5200,stroke-width:2px;")
        L.append("  class %s res;" % rid)
        out.append(("Shared Resource: %s" % c["resource"],
                    "%d services depend on this %s. None can migrate it "
                    "independently." % (c["member_count"], c["resource_kind"]),
                    "\n".join(L)))

    found = [p_["id"] for p_ in d["graph_metrics"]["per_node"]
             if p_["class"] == "Foundation" and nodes[p_["id"]]["kind"] == "internal"]
    if found:
        inb = collections.defaultdict(set)
        for e in d["edges"]:
            inb[e["target"]].add(e["source"])
        body, used = [], set()
        for f in sorted(found):
            deps = sorted(x for x in inb.get(f, ()) if nodes[x]["kind"] == "internal")
            if not deps:
                continue
            used.add(f); used.update(deps)
            for x in deps:
                body.append("  %s --> %s" % (x, f))
        if used:
            L = ["flowchart RL"] + [decl(i, nodes[i]) for i in sorted(used)] + body
            fnd = sorted(f for f in found if f in used)
            L.append("  classDef fnd fill:#eef7ee,stroke:#216e39,stroke-width:2px;")
            L.append("  class %s fnd;" % ",".join(fnd))
            out.append(("Foundation Services and Their Dependents",
                        "Services many others depend on. Everything pointing at a "
                        "green node waits on it.", "\n".join(L)))
    return out


# ------------------------------------------------------------------ render
def render_md(d, nodes):
    s, S, C = d["summary"], d, d["coverage"]["portfolio"]
    L = []
    a = L.append
    a(f"# Portfolio Inter-Application Dependency Report: {d['metadata']['portfolio_name']}\n")
    a(f"**Analysis date:** {d['metadata']['analysis_date']}  ")
    a(f"**Services analyzed:** {s['services_analyzed']}  ")
    a("**Source:** Per-repo Modernization Readiness Analysis reports  ")
    ep = C["edges_by_provenance"]
    a(f"**Edge provenance:** {ep.get('declared',0)} declared · "
      f"{ep.get('inferred_named',0)} inferred (named) · "
      f"{ep.get('inferred_shared_resource',0)} inferred (shared resource)\n")
    a("---\n")

    a("## Executive Summary\n")
    mb = s["max_blast_radius"]
    a(f"This analysis covers **{s['services_analyzed']} services** and found "
      f"**{s['app_to_app_edges']} application-to-application dependencies** plus "
      f"**{s['shared_resources']} shared resources** that couple services together. "
      f"The largest blast radius belongs to **{mb['node'] or 'n/a'}** "
      f"({mb['count']} dependent services, {mb['percent']}% of the portfolio).\n")
    a(f"There are **{s['circular_dependencies_app_to_app']} circular dependencies** between "
      f"applications and **{s['circular_dependencies_including_resources']}** once shared "
      f"resources are included. **{s['foundation_services']} foundation services** and "
      f"**{s['hub_services']} hub services** constrain the migration order, and the longest "
      f"dependency chain sets a floor of **{s['critical_path_length']} sequential waves**.\n")
    a(f"Coverage is uneven by construction. {C['good']} services have good dependency "
      f"coverage, {C['partial']} partial, {C['none']} had integration statements that could "
      f"not be resolved to a known service, and {C['silent']} had none at all. "
      f"**A service with no dependencies shown has not been shown to be independent** — see "
      f"Coverage and Confidence below before using this to sequence work.\n")

    a("## Dependency Overview\n")
    a("| Metric | Value |"); a("|---|---|")
    for k, v in [
        ("Services analyzed", s["services_analyzed"]),
        ("Application-to-application edges (observed)", s["app_to_app_edges"]),
        ("Shared-resource edges (observed)", s["shared_resource_edges"]),
        ("Derived service-to-service pairs (from shared resources)", s["derived_pairs"]),
        ("External systems identified", s["external_systems"]),
        ("Shared resources identified", s["shared_resources"]),
        ("Circular dependencies (app-to-app)", s["circular_dependencies_app_to_app"]),
        ("Circular dependencies (including shared resources)",
         s["circular_dependencies_including_resources"]),
        ("Foundation services", s["foundation_services"]),
        ("Hub services", s["hub_services"]),
        ("Critical path length (minimum waves)", s["critical_path_length"]),
        ("Services with no dependency data", s["services_without_dependency_data"]),
    ]:
        a(f"| {k} | {v} |")
    a("\n> Observed and derived edge counts are reported separately and are never summed. "
      "A shared resource with N consumers mechanically implies N·(N−1) service pairs; "
      "combining the two would overstate the number of distinct findings.\n")

    a("## Application Dependency Map\n")
    a("### Application-to-Application Dependencies\n")
    a("| Source | Target | Type | Protocol | Coupling | Provenance | Confidence | Evidence |")
    a("|---|---|---|---|---|---|---|---|")
    rank = {"High": 0, "Medium": 1, "Low": 2}
    aa = [e for e in S["edges"]
          if nodes[e["source"]]["kind"] == "internal"
          and nodes[e["target"]]["kind"] == "internal"]
    for e in sorted(aa, key=lambda e: (rank.get(e.get("coupling"), 3),
                                       nodes[e["source"]]["name"])):
        ev = e["evidence"][0] if e["evidence"] else {}
        a(f"| {cell(nodes[e['source']]['name'],60)} | {cell(nodes[e['target']]['name'],60)} "
          f"| {e['type']} | {cell(e.get('protocol'),20)} | {e.get('coupling','')} "
          f"| {e['provenance']} | {e['confidence']} "
          f"| {cell(str(ev.get('repo',''))+':'+str(ev.get('question_id','')),40)} |")
    if not aa:
        a("| — | — | — | — | — | — | — | — |")
        a("\n*No application-to-application dependencies resolved. See Coverage and Closable Gaps.*")

    a("\n### Dependencies on External Systems and Shared Resources\n")
    a("| Source | Target | Kind | Type | Protocol | Confidence | Evidence |")
    a("|---|---|---|---|---|---|---|")
    ex = [e for e in S["edges"] if nodes[e["target"]]["kind"] != "internal"]
    for e in sorted(ex, key=lambda e: nodes[e["target"]]["name"]):
        ev = e["evidence"][0] if e["evidence"] else {}
        a(f"| {cell(nodes[e['source']]['name'],50)} | {cell(nodes[e['target']]['name'],50)} "
          f"| {nodes[e['target']]['kind']}"
          f"{'/'+str(nodes[e['target']]['resource_kind']) if nodes[e['target']]['resource_kind'] else ''} "
          f"| {e['type']} | {cell(e.get('protocol'),20)} | {e['confidence']} "
          f"| {cell(str(ev.get('repo',''))+':'+str(ev.get('question_id','')),40)} |")
    if not ex:
        a("| — | — | — | — | — | — | — |")

    a("\n### Dependency Diagrams\n")
    blocks = mermaid_blocks(d, nodes)
    if not blocks:
        a("*No resolved dependencies to diagram.*")
    else:
        a(f"{len(blocks)} scoped views. A single diagram of all {len(nodes)} nodes would be "
          "unreadable, so the graph is split into the application call graph, each high-risk "
          "shared resource, and the foundation services with their dependents.\n")
        for title, note, src in blocks:
            a(f"#### {title}\n")
            a(f"{note}\n")
            a("```mermaid")
            a(src)
            a("```\n")

    a("\n## Service Dependency Metrics\n")
    a("| Service | Fan-in | Fan-out | Blast radius | Blast radius % | Class | Coverage |")
    a("|---|---:|---:|---:|---:|---|---|")
    cov = {c["id"]: c["coverage"] for c in d["coverage"]["per_service"]}
    for p in sorted(S["graph_metrics"]["per_node"],
                    key=lambda p: -p["blast_radius_count"]):
        if nodes[p["id"]]["kind"] != "internal":
            continue
        a(f"| {cell(nodes[p['id']]['name'],60)} | {p['fan_in']} | {p['fan_out']} "
          f"| {p['blast_radius_count']} | {p['blast_radius_percent']} | {p['class']} "
          f"| {cov.get(p['id'],'—')} |")

    for title, cls, note in [
        ("Foundation Services", "Foundation",
         "Many services depend on these and they depend on little. Modernize them first — "
         "everything downstream waits on them."),
        ("Hub Services", "Hub",
         "High fan-in **and** high fan-out. These are the highest-risk nodes in the estate: "
         "they cannot move early (they depend on much) or late (much depends on them)."),
    ]:
        a(f"\n### {title}\n")
        rows = [p for p in S["graph_metrics"]["per_node"] if p["class"] == cls]
        if not rows:
            a(f"*None identified.*")
            continue
        a(note + "\n")
        a("| Service | Fan-in | Fan-out | Blast radius |"); a("|---|---:|---:|---:|")
        for p in sorted(rows, key=lambda p: -p["fan_in"]):
            a(f"| {cell(nodes[p['id']]['name'],60)} | {p['fan_in']} | {p['fan_out']} "
              f"| {p['blast_radius_count']} ({p['blast_radius_percent']}%) |")

    a("\n## Shared Resource Clusters\n")
    if S["shared_resource_clusters"]:
        a("| Resource | Kind | Members | Coordination risk |")
        a("|---|---|---:|---|")
        for c in S["shared_resource_clusters"]:
            a(f"| {cell(c['resource'],60)} | {c['resource_kind']} | {c['member_count']} "
              f"| {c['coordination_risk']} |")
        for c in S["shared_resource_clusters"]:
            if c["coordination_risk"] == "High":
                a(f"\n### {c['resource']} — {c['member_count']} services\n")
                a(", ".join(c["member_services"]))
                a(f"\nA {c['resource_kind']} shared by {c['member_count']} services cannot be "
                  "migrated by any one of them independently. Sequence the decoupling work "
                  "(schema split, read-model extraction, or API interposition) before the "
                  "member services move.")
    else:
        a("*No resource was found to be shared by 2 or more services.*")
    if S.get("dropped_clusters"):
        a("\n**Clusters dropped as implausible** (exceeded "
          f"{int(OVERSIZE_FRACTION*100)}% of the portfolio, indicating a generic "
          "technology name rather than a named instance):\n")
        a("| Resource | Members | Reason |"); a("|---|---:|---|")
        for x in S["dropped_clusters"]:
            a(f"| {cell(x['resource'],50)} | {x['members']} | {cell(x['reason'],70)} |")

    a("\n## Circular Dependencies\n")
    for key, title, note in [
        ("app_to_app", "Application-to-Application Cycles",
         "Direct call loops. Unambiguous architectural problems."),
        ("including_resources", "Cycles Through Shared Resources",
         "Coordination constraints, **not** call loops. Two services that both read and "
         "write the same store form a cycle through it; neither calls the other, but neither "
         "can migrate its schema independently. The remedy is splitting data ownership, not "
         "breaking a call."),
    ]:
        a(f"\n### {title}\n")
        cyc = S["circular_dependencies"][key]
        if not cyc:
            a("*None detected in the resolved graph. Note that undetected dependencies "
              "cannot produce detected cycles — see Coverage.*")
            continue
        a(note + "\n")
        a("| Cycle | Services | Lowest confidence |"); a("|---|---|---|")
        for n, c in enumerate(cyc, 1):
            a(f"| {n} | {cell(' → '.join(c['services']),110)} "
              f"| {c.get('lowest_confidence','—')} |")

    a("\n## Critical Path\n")
    cp = S["critical_path"]
    if cp["length"]:
        a(" → ".join(f"`{x}`" for x in cp["nodes"]) + "\n")
        a(f"This chain sets a floor of **{cp['length']} sequential migration waves**. "
          "Adding delivery capacity parallelizes work within a wave; it cannot reduce the "
          "number of waves.")
    else:
        a("*No multi-node dependency chain resolved.*")

    a("\n## Dependency-Aware Migration Waves\n")
    a("### Sequencing Principles\n")
    for n, p in enumerate([
        "Dependencies are modernized no later than their dependents.",
        "Foundation services, hub services, and any service in a cycle go first — nothing "
        "downstream can be safely sequenced until they are addressed.",
        "Shared resources with high coordination risk are decoupled before their member "
        "services move.",
        "Services with no dependency data are sequenced by business priority alone and "
        "flagged — absence of edges is not evidence of independence.",
    ], 1):
        a(f"{n}. {p}")
    for w in S["migration_waves"]:
        label = (f"### Wave {w['wave']} — {w['name']}" if w["wave"] is not None
                 else f"### Wave ∞ — {w['name']}")
        a(f"\n{label} ({w['service_count']} services)\n")
        a("| Service | Reason | Priority | Blast radius |"); a("|---|---|---|---:|")
        for sv in w["services"]:
            a(f"| {cell(sv['service'],60)} | {sv['reason']} | {sv['priority'] or '—'} "
              f"| {sv['blast_radius']} |")
        if len(w["parallel_tracks"]) > 1:
            a(f"\n**Parallelizable tracks in this wave:** {len(w['parallel_tracks'])} "
              "independent groups that can run concurrently.\n")
            a("| Track | Services | Count |"); a("|---|---|---:|")
            for t in w["parallel_tracks"]:
                a(f"| {t['track']} | {cell(', '.join(t['services']),110)} | {t['count']} |")

    a("\n### Sequencing Validation\n")
    a("| Assertion | Result |"); a("|---|---|")
    for k, v in S["sequencing_validation"]["assertions"].items():
        a(f"| {k} | {'Pass' if v else 'FAIL'} |")
    if not S["sequencing_validation"]["sequencing_valid"]:
        a("\n**Sequencing validation failed.** The wave plan is emitted as computed, without "
          "reordering to force a pass — a failure means the graph contains something the "
          "sequencer could not model, and hiding it would still leave a plan someone follows.")

    a("\n## Coverage and Confidence\n")
    a("### Portfolio Coverage\n")
    a("| Coverage | Services | Meaning |"); a("|---|---:|---|")
    for k, lbl in [("good", "Good"), ("partial", "Partial"),
                   ("none", "None"), ("silent", "Silent")]:
        meaning = {"good": "3+ resolved edges, or a declared edge",
                   "partial": "1–2 resolved edges",
                   "none": "Integration signals found but unresolved",
                   "silent": "No integration signals in the reports"}[k]
        a(f"| {lbl} | {C[k]} | {meaning} |")
    a("\n> **`Silent` does not mean independent.** It means these services' MOD findings did "
      "not describe their integrations. MOD describes integrations incidentally, while scoring "
      "something else, so silence is a reporting gap rather than an architectural fact. Do not "
      "treat a Silent service as a safe first migration candidate on the strength of this "
      "report alone.\n")

    a("### Edge Confidence Distribution\n")
    a("| Confidence | Edges |"); a("|---|---:|")
    for k in ("high", "medium", "low"):
        a(f"| {k.title()} | {C['edges_by_confidence'].get(k,0)} |")

    a("\n### Per-Service Coverage\n")
    a("| Service | Edges | Signals | Unresolved | MD | Coverage |")
    a("|---|---:|---:|---:|---|---|")
    for c in sorted(d["coverage"]["per_service"],
                    key=lambda c: ({"Silent": 0, "None": 1, "Partial": 2, "Good": 3}
                                   [c["coverage"]], c["id"])):
        a(f"| {cell(nodes[c['id']]['name'],60)} | {c['edge_count']} | {c['signals_found']} "
          f"| {c['unresolved_signals']} | {'Yes' if c['md_available'] else 'No'} "
          f"| {c['coverage']} |")

    a("\n### Unresolved Signals\n")
    us = S["unresolved_signals"]
    if us:
        by = collections.Counter(u.get("reason") for u in us)
        a("| Reason | Count | Closable by |"); a("|---|---:|---|")
        fix = {"no_alias_match": "`service_aliases` or `external_systems`",
               "ambiguous_alias": "`service_aliases` (disambiguate)",
               "mechanism_unclear": "`dependency_overrides`",
               "generic_name": "nothing — expected noise"}
        for r, n in by.most_common():
            a(f"| {r} | {n} | {fix.get(r,'—')} |")
        a("\n| Source repo | Question | Candidate | Reason |")
        a("|---|---|---|---|")
        for u in us[:60]:
            a(f"| {cell(u.get('source_repo'),40)} | {cell(u.get('question_id'),14)} "
              f"| {cell(', '.join(u.get('candidate_names') or []),44)} "
              f"| {u.get('reason','')} |")
        if len(us) > 60:
            a(f"\n*{len(us)-60} further unresolved signals are in the JSON artifact.*")
    else:
        a("*None.*")

    a("\n### Alias Collisions\n")
    if S["alias_collisions"]:
        a("| Match key | Competing services |"); a("|---|---|")
        for c in S["alias_collisions"][:40]:
            a(f"| `{cell(c['match_key'],40)}` "
              f"| {cell(', '.join(c['competing_services']),90)} |")
    else:
        a("*None.*")

    a("\n### Derived Naming Prefixes\n")
    pf = S["graph_metrics"]["portfolio"]["derived_naming_prefixes"]
    a(f"Prefixes derived from the repository inventory, used for name matching: "
      f"{', '.join('`'+p+'`' for p in pf) if pf else '*none derived*'}.\n")

    a("## Closable Gaps\n")
    cg = S["closable_gaps"]
    if cg:
        a("| Priority | Gap | Blocked signals | Recommended entry |")
        a("|---:|---|---:|---|")
        for n, g in enumerate(cg[:40], 1):
            a(f"| {n} | {cell(g.get('gap'),60)} | {g.get('blocked_signals',0)} "
              f"| {cell(g.get('recommended_entry'),80)} |")
        a("\nClose the top rows in `atx-config.yaml` and re-run. The second run is materially "
          "better than the first.")
    else:
        a("*No closable gaps identified.*")

    a("\n## Methodology and Limitations\n")
    a(f"This graph is mined from MOD report prose written to score modernization readiness, "
      f"not to document architecture. Coverage is therefore uneven by construction. No "
      f"repository source code was scanned; all findings derive from per-repo MOD JSON "
      f"`findings[]` prose fields and per-repo Markdown `## Detailed Findings` sections.\n")
    a(f"{d['metadata']['reports_consumed']} per-repo MOD reports were consumed; "
      f"{d['metadata']['reports_excluded']} were excluded. "
      f"{d['metadata']['md_enrichment_available']} had Markdown available for enrichment.\n")
    a("**The absence of an edge is not evidence of independence.** `dependency_overrides` in "
      "`additionalPlanContext` is the supported path for authoritative dependency data.\n")

    a("## Appendix: Services Analyzed\n")
    a("| Service | Repo directory | Tier | Score | Archetype | Priority | MD |")
    a("|---|---|---|---:|---|---|---|")
    for i, n in sorted(nodes.items(), key=lambda kv: kv[1]["name"].lower()):
        if n["kind"] != "internal":
            continue
        a(f"| {cell(n['name'],50)} | {cell(n['repo_dir'],40)} | {cell(n['tier'],24)} "
          f"| {n['overall_score'] if n['overall_score'] is not None else '—'} "
          f"| {cell(n['service_archetype'],22)} | {n['repository_priority'] or '—'} "
          f"| {'Yes' if n['md_available'] else 'No'} |")
    return "\n".join(L) + "\n"


def diagrams_panel(d, nodes):
    blocks = mermaid_blocks(d, nodes)
    if not blocks:
        return "<p class='muted'>No resolved dependencies to diagram.</p>"
    parts = [
        "<p>Mermaid source for each view. Paste a block into "
        "<code>mermaid.live</code>, any Mermaid-aware Markdown viewer, or see the "
        "same diagrams rendered in the <code>.md</code> report. They are also in the "
        "<code>.diagrams.mmd</code> file next to this one.</p>",
        "<p class='muted'>Kept as source rather than pictures so this file stays "
        "fully self-contained \u2014 no network fetch at render time.</p>",
    ]
    for n, (title, note, src) in enumerate(blocks):
        parts.append(
            f'<h3>{esc(title)}</h3><p class="muted">{esc(note)}</p>'
            f'<button class="copy" onclick="cp({n})">Copy</button>'
            f'<pre class="mmd" id="mmd{n}">{esc(src)}</pre>')
    return "".join(parts)


def render_html(d, nodes):
    s, C = d["summary"], d["coverage"]["portfolio"]
    pn = esc(d["metadata"]["portfolio_name"])

    def donut(vals, labels, colors):
        tot = sum(vals) or 1
        segs, off, r, cc = [], 0.0, 54, 2 * 3.14159 * 54
        for v, c in zip(vals, colors):
            ln = cc * v / tot
            segs.append(f'<circle r="{r}" cx="70" cy="70" fill="transparent" '
                        f'stroke="{c}" stroke-width="26" '
                        f'stroke-dasharray="{ln:.2f} {cc-ln:.2f}" '
                        f'stroke-dashoffset="{-off:.2f}" transform="rotate(-90 70 70)"/>')
            off += ln
        lg = "".join(
            f'<div class="lg"><span class="sw" style="background:{c}"></span>'
            f'{esc(l)} <b>{v}</b></div>'
            for v, l, c in zip(vals, labels, colors) if v)
        return (f'<div class="chartrow"><svg viewBox="0 0 140 140" width="150" '
                f'height="150">{"".join(segs)}</svg><div>{lg}</div></div>')

    def bars(rows):
        if not rows:
            return "<p class='muted'>No blast radius data.</p>"
        mx = max(r[1] for r in rows) or 1
        out = []
        for name, v, p in rows:
            out.append(
                f'<div class="bar"><div class="bl">{esc(name)}</div>'
                f'<div class="bt"><div class="bf" style="width:{100*v/mx:.1f}%"></div></div>'
                f'<div class="bv">{v} <span class="muted">({p}%)</span></div></div>')
        return "".join(out)

    def table(headers, rows, tid):
        th = "".join(f"<th>{esc(h)}</th>" for h in headers)
        tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                     for r in rows) or \
             f'<tr><td colspan="{len(headers)}" class="muted">No rows.</td></tr>'
        return (f'<div class="tw"><table id="{tid}"><thead><tr>{th}</tr></thead>'
                f'<tbody>{tr}</tbody></table></div>')

    per = {p["id"]: p for p in d["graph_metrics"]["per_node"]}
    cov = {c["id"]: c for c in d["coverage"]["per_service"]}

    dep_rows = [[esc(nodes[e["source"]]["name"]), esc(nodes[e["target"]]["name"]),
                 esc(nodes[e["target"]]["kind"]), esc(e["type"]),
                 esc(e.get("protocol") or "—"), esc(e.get("coupling") or "—"),
                 f'<span class="pill {esc(e["confidence"])}">{esc(e["confidence"])}</span>',
                 esc((e["evidence"][0].get("raw_text") if e["evidence"] else "") or "")[:300]]
                for e in sorted(d["edges"],
                                key=lambda e: ({"High": 0, "Medium": 1, "Low": 2}
                                               .get(e.get("coupling"), 3),
                                               nodes[e["source"]]["name"]))]

    svc_rows = [[esc(n["name"]), str(per[i]["fan_in"]), str(per[i]["fan_out"]),
                 str(per[i]["blast_radius_count"]),
                 f'{per[i]["blast_radius_percent"]}%', esc(per[i]["class"]),
                 esc(n["tier"] or "—"), esc(n["repository_priority"] or "—"),
                 f'<span class="pill cov-{esc(cov.get(i,{}).get("coverage","—"))}">'
                 f'{esc(cov.get(i,{}).get("coverage","—"))}</span>']
                for i, n in sorted(nodes.items(),
                                   key=lambda kv: -per[kv[0]]["blast_radius_count"])
                if n["kind"] == "internal"]

    res_rows = [[esc(c["resource"]), esc(c["resource_kind"]), str(c["member_count"]),
                 f'<span class="pill r-{esc(c["coordination_risk"])}">'
                 f'{esc(c["coordination_risk"])}</span>',
                 esc(", ".join(c["member_services"]))[:400]]
                for c in d["shared_resource_clusters"]]

    cyc_rows = ([[esc(k.replace("_", " ")), esc(" → ".join(c["services"])),
                  esc(c.get("lowest_confidence") or "—")]
                 for k in ("app_to_app", "including_resources")
                 for c in d["circular_dependencies"][k]])

    wav_rows = [[("∞" if w["wave"] is None else str(w["wave"])), esc(sv["service"]),
                 esc(sv["reason"]), esc(sv["priority"] or "—"), str(sv["blast_radius"]),
                 esc(per[nid(sv['service'])]["class"]
                     if nid(sv['service']) in per else "—")]
                for w in d["migration_waves"] for sv in w["services"]]

    gap_rows = [[str(n), esc(g.get("gap")), str(g.get("blocked_signals", 0)),
                 esc(g.get("recommended_entry"))]
                for n, g in enumerate(d["closable_gaps"][:60], 1)]

    tabs = [
        ("Dependencies", table(["Source", "Target", "Target kind", "Type", "Protocol",
                                "Coupling", "Confidence", "Evidence"], dep_rows, "t1")),
        ("Services", table(["Service", "Fan-in", "Fan-out", "Blast radius", "%",
                            "Class", "Tier", "Priority", "Coverage"], svc_rows, "t2")),
        ("Shared Resources", table(["Resource", "Kind", "Members", "Coordination risk",
                                    "Member services"], res_rows, "t3")),
        ("Cycles", table(["Scope", "Cycle", "Lowest confidence"], cyc_rows, "t4")),
        ("Waves", table(["Wave", "Service", "Reason", "Priority", "Blast radius",
                         "Class"], wav_rows, "t5")),
        ("Closable Gaps", table(["#", "Gap", "Blocked signals", "Recommended entry"],
                                gap_rows, "t6")),
        ("Diagrams", diagrams_panel(d, nodes)),
    ]
    tb = "".join(f'<button class="tab{" on" if n==0 else ""}" '
                 f'onclick="pick({n})">{esc(t)}</button>'
                 for n, (t, _) in enumerate(tabs))
    tp = "".join(f'<div class="panel{" on" if n==0 else ""}">{c}</div>'
                 for n, (_, c) in enumerate(tabs))

    top = sorted((p for p in d["graph_metrics"]["per_node"]
                  if p["blast_radius_count"] > 0),
                 key=lambda p: -p["blast_radius_count"])[:10]
    bar_rows = [(nodes[p["id"]]["name"], p["blast_radius_count"],
                 p["blast_radius_percent"]) for p in top]

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Inter-Application Dependencies — {pn}</title><style>
*{{box-sizing:border-box}}
body{{margin:0;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:#16191f;background:#f7f8f8}}
header{{background:#232f3e;color:#fff;padding:22px 28px}}
header h1{{margin:0;font-size:21px}}
header .sub{{color:#d5dbdb;font-size:13px;margin-top:5px}}
main{{max-width:1340px;margin:0 auto;padding:22px 28px 60px}}
.card{{background:#fff;border:1px solid #e3e5e5;border-radius:8px;padding:18px 20px;margin-bottom:18px}}
.card h2{{margin:0 0 10px;font-size:16px;color:#0f1b2a}}
.card h3{{margin:14px 0 6px;font-size:14px;color:#232f3e}}
.stats{{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:18px}}
.stat{{flex:1 1 180px;background:#fff;border:1px solid #e3e5e5;border-left:4px solid #ff9900;border-radius:8px;padding:14px 16px}}
.stat .v{{font-size:26px;font-weight:700;color:#0f1b2a}}
.stat .l{{font-size:12px;color:#5f6b7a;margin-top:2px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
@media(max-width:900px){{.grid2{{grid-template-columns:1fr}}}}
.chartrow{{display:flex;align-items:center;gap:20px;flex-wrap:wrap}}
.lg{{font-size:12.5px;margin:3px 0}}
.sw{{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px}}
.bar{{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:12.5px}}
.bl{{width:230px;text-align:right;color:#232f3e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bt{{flex:1;background:#eef0f1;height:16px;border-radius:3px;overflow:hidden}}
.bf{{height:100%;background:#ff9900}}
.bv{{width:92px;font-variant-numeric:tabular-nums}}
.tabs{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:0}}
.tab{{background:#eef0f1;border:1px solid #e3e5e5;border-bottom:none;border-radius:6px 6px 0 0;padding:8px 14px;cursor:pointer;font-size:13px;font-weight:600;color:#5f6b7a}}
.tab.on{{background:#fff;color:#0f1b2a;box-shadow:inset 0 3px 0 #ff9900}}
.panel{{display:none;background:#fff;border:1px solid #e3e5e5;border-radius:0 8px 8px 8px;padding:14px}}
.panel.on{{display:block}}
.tw{{overflow-x:auto;max-height:620px}}
table{{border-collapse:collapse;width:100%;font-size:12.5px}}
th{{background:#232f3e;color:#fff;text-align:left;padding:7px 9px;position:sticky;top:0;white-space:nowrap}}
td{{border-bottom:1px solid #eef0f1;padding:6px 9px;vertical-align:top}}
tr:nth-child(even) td{{background:#fbfbfb}}
.pill{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600}}
.pill.high,.pill.r-High{{background:#fdecea;color:#a4161a}}
.pill.medium,.pill.r-Medium{{background:#fff4e0;color:#8a5200}}
.pill.low,.pill.r-Low{{background:#eef7ee;color:#216e39}}
.pill.cov-Good{{background:#eef7ee;color:#216e39}}
.pill.cov-Partial{{background:#fff4e0;color:#8a5200}}
.pill.cov-None{{background:#fdecea;color:#a4161a}}
.pill.cov-Silent{{background:#eceff1;color:#455a64}}
.warn{{background:#fffaf0;border-left:4px solid #ff9900;padding:11px 15px;border-radius:0 6px 6px 0;margin:12px 0}}
.muted{{color:#5f6b7a}}
pre.mmd{{background:#f7f8f8;border:1px solid #e3e5e5;border-radius:6px;padding:11px 13px;font:11.5px/1.45 "SF Mono",Menlo,monospace;overflow-x:auto;max-height:330px;white-space:pre}}
button.copy{{float:right;background:#232f3e;color:#fff;border:0;border-radius:5px;padding:4px 11px;font-size:11.5px;cursor:pointer}}
footer{{text-align:center;color:#5f6b7a;font-size:12px;padding:22px}}
</style></head><body>
<header><h1>Inter-Application Dependencies — {pn}</h1>
<div class="sub">{esc(d['metadata']['analysis_date'])} · {s['services_analyzed']} services ·
derived from Modernization Readiness Analysis</div></header>
<main>

<div class="card"><h2>Executive Summary</h2>
<h3>Dependency Landscape</h3>
<p>{s['app_to_app_edges']} application-to-application dependencies were resolved across
{s['services_analyzed']} services, alongside {s['shared_resources']} shared resources and
{s['external_systems']} external systems. Shared-resource coupling implies a further
{s['derived_pairs']} service pairs, reported separately and never added to the observed count.</p>
<h3>Highest-Risk Nodes</h3>
<p>{s['foundation_services']} foundation services and {s['hub_services']} hub services constrain
the order of work. The largest blast radius is
<b>{esc(s['max_blast_radius']['node'] or 'n/a')}</b> at {s['max_blast_radius']['count']} dependent
services ({s['max_blast_radius']['percent']}% of the portfolio).
{s['circular_dependencies_app_to_app']} application-to-application cycles and
{s['circular_dependencies_including_resources']} resource-mediated cycles were detected.</p>
<h3>Sequencing Implications</h3>
<p>The longest dependency chain sets a floor of <b>{s['critical_path_length']} sequential
waves</b>. Adding teams parallelizes work within a wave but cannot reduce the wave count.</p>
<div class="warn"><b>Coverage caveat.</b> This graph is mined from report prose written to score
modernization readiness, not to document architecture, so coverage is uneven by construction.
{C['good']} services have good coverage, {C['partial']} partial, {C['none']} had integration
statements that could not be matched to a known service, and {C['silent']} had none at all.
<b>A service shown with no dependencies has not been shown to be independent</b> — treat the
Coverage column as load-bearing before using this to decide what moves first.</div>
</div>

<div class="stats">
<div class="stat"><div class="v">{s['services_analyzed']}</div><div class="l">Services Analyzed</div></div>
<div class="stat"><div class="v">{s['app_to_app_edges']}</div><div class="l">App-to-App Dependencies</div></div>
<div class="stat"><div class="v">{s['shared_resources']}</div><div class="l">Shared Resources</div></div>
<div class="stat"><div class="v">{s['circular_dependencies_app_to_app']}</div><div class="l">Circular Dependencies</div></div>
<div class="stat"><div class="v">{s['critical_path_length']}</div><div class="l">Minimum Waves</div></div>
</div>

<div class="grid2">
<div class="card"><h2>Coverage Distribution</h2>
{donut([C['good'],C['partial'],C['none'],C['silent']],
       ['Good','Partial','None','Silent'],
       ['#216e39','#e8a33d','#c0392b','#90a4ae'])}</div>
<div class="card"><h2>Top 10 Blast Radius</h2>{bars(bar_rows)}</div>
</div>

<div class="tabs">{tb}</div>{tp}

</main>
<footer>Generated by AWS Transform · Portfolio Inter-Application Dependency Analysis<br>
© {datetime.date.today().year} Amazon Web Services, Inc. All rights reserved.</footer>
<script>
function cp(n){{
  const t=document.getElementById('mmd'+n).textContent;
  navigator.clipboard&&navigator.clipboard.writeText(t);
}}
function pick(n){{
  document.querySelectorAll('.tab').forEach((t,i)=>t.classList.toggle('on',i===n));
  document.querySelectorAll('.panel').forEach((p,i)=>p.classList.toggle('on',i===n));
}}
</script></body></html>
"""


# -------------------------------------------------------------------- main
def main():
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    root = os.path.abspath(sys.argv[1])
    work = os.path.join(root, ".iad-work")
    try:
        corpus = json.load(open(os.path.join(work, "corpus.json"), encoding="utf-8"))
    except OSError:
        sys.stderr.write(f"\nFATAL: {work}/corpus.json not found. "
                         f"Run prepare_corpus.py first.\n")
        return 1
    try:
        spec = json.load(open(os.path.join(work, "edges.json"), encoding="utf-8"))
    except OSError:
        sys.stderr.write(f"\nFATAL: {work}/edges.json not found. The agent must write it "
                         f"before rendering. See this script's docstring for the schema.\n")
        return 1

    name = spec.get("portfolio_name") or corpus.get("portfolio_dir_name") or "portfolio"
    # ‼ Collapse to a bare basename FIRST. portfolio_name arrives from edges.json /
    # additionalPlanContext, so a value like "../../tmp/x" would otherwise write the four
    # artifacts outside the working directory -- contradicting this TD's own guarantee
    # that the only writes are its own outputs. [\s_]+ does not strip "/" or "..".
    name = os.path.basename(str(name).strip()) or "portfolio"
    name = re.sub(r"[^A-Za-z0-9.-]+", "-", name.lower()).strip("-.") or "portfolio"
    src = spec.get("portfolio_name_source") or (
        "supplied" if spec.get("portfolio_name") else "derived_from_workdir")

    nodes, by_key, slug_to_id = build_nodes(corpus, spec)
    edges, dangling, malformed = build_edges(spec, nodes, by_key)
    if malformed:
        sys.stderr.write(
            f"\nFATAL: {len(malformed)} edge(s) have no usable type. Every edge needs "
            f'"type" (or "edge") set to one of {list(EDGE_TYPES)}.\n')
        for x in malformed[:20]:
            sys.stderr.write(f"  edges[{x['index']}] {x['source']!r} -> {x['target']!r}: "
                             f"type_found={x['type_found']!r} keys={x['keys_present']}\n")
        if len(malformed) > 20:
            sys.stderr.write(f"  ... and {len(malformed)-20} more\n")
        sys.stderr.write("\nFix edges.json and re-run. Nothing was written.\n")
        return 1
    if dangling:
        sys.stderr.write(f"\nFATAL: {len(dangling)} dangling edge endpoint(s) "
                         f"(no matching node). Declare external systems and shared "
                         f"resources in extra_nodes before referencing them.\n")
        for x in dangling[:20]:
            sys.stderr.write(f"  edges[{x['index']}] {x['source']!r} -> {x['target']!r}\n")
        if len(dangling) > 20:
            sys.stderr.write(f"  ... and {len(dangling)-20} more\n")
        sys.stderr.write("\nFix edges.json and re-run. Nothing was written.\n")
        return 1

    internal = {i for i, n in nodes.items() if n["kind"] == "internal"}
    clusters, derived, dropped = clusters_and_derived(edges, nodes, len(internal))

    # recompute metrics over observed + derived (02-graph-metrics.md 5)
    all_edges = edges + derived
    per, _ = metrics(all_edges, nodes, observed=edges)

    adj_app = collections.defaultdict(set)
    for e in edges:
        if e["source"] in internal and e["target"] in internal:
            adj_app[e["source"]].add(e["target"])
    adj_all = collections.defaultdict(set)
    for e in all_edges:
        adj_all[e["source"]].add(e["target"])

    def mk(cycles, pool):
        out = []
        for c in cycles:
            ce = [e for e in pool
                  if e["source"] in c and e["target"] in c]
            cr = {"high": 0, "medium": 1, "low": 2}
            lc = min((e["confidence"] for e in ce),
                     key=lambda x: -cr.get(x, 1), default="medium")
            out.append({"services": [nodes[x]["name"] for x in c],
                        "service_ids": c, "lowest_confidence": lc,
                        "edge_count": len(ce)})
        return out

    cyc_app = tarjan(internal, adj_app)
    cyc_all = tarjan(set(nodes), adj_all)
    cp = critical_path(edges, nodes, cyc_app)
    wv, assigned, unseq, w0 = waves(edges, nodes, per, cyc_app, clusters)

    # coverage (Step 7)
    pm = {p["id"]: p for p in per}
    snips = {s["slug"]: s.get("signal_count", len(s.get("signal_snippets") or []))
             for s in corpus["services"]}
    unres = collections.Counter(u.get("source_repo") for u in spec.get("unresolved_signals") or [])
    per_cov = []
    for s in corpus["services"]:
        i = slug_to_id[s["slug"]]
        n_e = pm[i]["fan_in"] + pm[i]["fan_out"]
        declared = any(e["provenance"] == "declared"
                       and i in (e["source"], e["target"]) for e in edges)
        sig = snips.get(s["slug"], 0)
        c = ("Good" if (n_e >= 3 or declared) else
             "Partial" if n_e >= 1 else
             "None" if sig else "Silent")
        per_cov.append({"id": i, "edge_count": n_e, "inbound_count": pm[i]["fan_in"],
                        "outbound_count": pm[i]["fan_out"], "signals_found": sig,
                        "unresolved_signals": unres.get(s["repo_name"], 0)
                        or unres.get(s["slug"], 0),
                        "md_available": s["md_available"], "coverage": c})
    cc = collections.Counter(c["coverage"] for c in per_cov)

    a2a = [e for e in edges
           if nodes[e["source"]]["kind"] == "internal"
           and nodes[e["target"]]["kind"] == "internal"]
    srz = [e for e in edges if nodes[e["target"]]["kind"] == "resource"]
    mb = max(per, key=lambda p: p["blast_radius_count"]) if per else None

    # Longest dependency chain among services the sequencer actually ordered.
    seq_internal = {i for i in internal if i not in w0}
    seq_adj = collections.defaultdict(set)
    for e in edges:
        if e["source"] in seq_internal and e["target"] in seq_internal:
            seq_adj[e["source"]].add(e["target"])
    _depth_memo = {}

    def _depth(v, stack):
        if v in _depth_memo:
            return _depth_memo[v]
        if v in stack:
            return 0
        best = 0
        for w in seq_adj.get(v, ()):
            best = max(best, _depth(w, stack | {v}))
        _depth_memo[v] = 1 + best
        return _depth_memo[v]

    seq_depth = max([_depth(v, frozenset()) for v in seq_internal] or [0])
    seq_depth += 1 if w0 else 0

    asserts = {
        "Dependencies placed no later than dependents": all(
            assigned.get(e["target"], 0) <= assigned.get(e["source"], 0)
            for e in edges
            if e["source"] in assigned and e["target"] in assigned
            and e["source"] not in w0 and e["target"] not in w0),
        "Every service placed exactly once": len(assigned) + len(unseq) == len(internal),
        # The floor on wave count is the longest chain the SEQUENCER had to lay
        # out -- i.e. among non-Wave-0 services -- plus one for Wave 0 itself.
        # Comparing against the whole-graph critical path is wrong: Wave 0 pulls
        # foundations and cycle members out first, which legitimately breaks long
        # chains and shortens the remainder.
        "Wave count >= sequenced chain depth":
            max([w["wave"] for w in wv if w["wave"] is not None] or [0]) + 1
            >= seq_depth,
        "No Wave 0 service duplicated in later waves": all(
            assigned[i] == 0 for i in w0 if i in assigned),
    }

    d = {
        "analysis_type": "portfolio-interapp-dep",
        "metadata": {
            "portfolio_name": name,
            "analysis_date": datetime.date.today().isoformat(),
            "td_version": TD_VERSION,
            "portfolio_name_source": src,
            "source_analysis_type": "modernization-readiness",
            "reports_consumed": corpus["counts"]["services"],
            "reports_excluded": corpus["counts"]["excluded_reports"],
            "md_enrichment_available": corpus["counts"]["md_available"],
            "context": spec.get("context"),
        },
        "summary": {
            "services_analyzed": len(internal),
            "app_to_app_edges": len(a2a),
            "shared_resource_edges": len(srz),
            "derived_pairs": len(derived),
            "external_systems": sum(1 for n in nodes.values() if n["kind"] == "external"),
            "shared_resources": len(clusters),
            "circular_dependencies_app_to_app": len(cyc_app),
            "circular_dependencies_including_resources": len(cyc_all),
            "foundation_services": sum(1 for p in per if p["class"] == "Foundation"),
            "hub_services": sum(1 for p in per if p["class"] == "Hub"),
            "critical_path_length": cp["length"],
            "max_blast_radius": {
                "node": nodes[mb["id"]]["name"] if mb else None,
                "count": mb["blast_radius_count"] if mb else 0,
                "percent": mb["blast_radius_percent"] if mb else 0.0},
            "services_without_dependency_data": cc["None"] + cc["Silent"],
        },
        "filter_vocab": {
            "edge_types": [t for t in EDGE_TYPES if any(e["type"] == t for e in all_edges)],
            "node_kinds": sorted({n["kind"] for n in nodes.values()}),
            "provenance": sorted({e["provenance"] for e in all_edges}),
            "confidence": [c for c in ("high", "medium", "low")
                           if any(e["confidence"] == c for e in all_edges)],
            "coupling": [c for c in ("High", "Medium", "Low")
                         if any(e.get("coupling") == c for e in all_edges)],
            "coverage": [c for c in ("Good", "Partial", "None", "Silent") if cc[c]],
            "node_classes": sorted({p["class"] for p in per} - {"none"}),
        },
        "nodes": [nodes[i] for i in sorted(nodes)],
        "edges": edges,
        "derived_edges": derived,
        "shared_resource_clusters": clusters,
        "dropped_clusters": dropped,
        "graph_metrics": {
            "per_node": per,
            "portfolio": {
                "internal_node_count": len(internal),
                "edge_density": round(len(a2a) / max(1, len(internal) * (len(internal) - 1)), 5),
                "largest_scc_size": max([len(c) for c in cyc_all] or [0]),
                "derived_naming_prefixes": corpus["derived_naming_prefixes"],
            },
        },
        "circular_dependencies": {"app_to_app": mk(cyc_app, edges),
                                  "including_resources": mk(cyc_all, all_edges)},
        "critical_path": cp,
        "migration_waves": wv,
        "sequencing_validation": {"sequencing_valid": all(asserts.values()),
                                  "assertions": asserts,
                                  "unsequenceable": [nodes[i]["name"] for i in unseq]},
        "coverage": {"per_service": per_cov,
                     "portfolio": {
                         "good": cc["Good"], "partial": cc["Partial"],
                         "none": cc["None"], "silent": cc["Silent"],
                         "edges_by_provenance": dict(collections.Counter(
                             e["provenance"] for e in edges)),
                         "edges_by_confidence": dict(collections.Counter(
                             e["confidence"] for e in edges)),
                         "md_available_count": corpus["counts"]["md_available"],
                         "unresolved_signal_count": len(spec.get("unresolved_signals") or []),
                         "alias_collision_count": len(corpus["alias_collisions"]),
                     }},
        "unresolved_signals": spec.get("unresolved_signals") or [],
        "alias_collisions": corpus["alias_collisions"],
        "closable_gaps": spec.get("closable_gaps") or [],
        "excluded_reports": corpus["excluded_reports"],
    }

    # --- Step 4 completeness guard -------------------------------------------
    # A batch silently skipped during classification (e.g. delegated to a
    # research-only subagent that cannot write) leaves its services with no
    # edges AND no unresolved signals. That is indistinguishable from "genuinely
    # has no dependencies" in the output, so check it explicitly and say so.
    touched = set()
    for e in edges:
        touched.add(e["source"]); touched.add(e["target"])
    for u in spec.get("unresolved_signals") or []:
        r = resolve(u.get("source_repo"), nodes, by_key)
        if r:
            touched.add(r)
    unprocessed = sorted(
        nodes[slug_to_id[s["slug"]]]["name"]
        for s in corpus["services"]
        if snips.get(s["slug"], 0) > 0 and slug_to_id[s["slug"]] not in touched)
    batch_cov = []
    for b in corpus.get("signal_batches") or []:
        try:
            bd = json.load(open(os.path.join(work, b["file"]), encoding="utf-8"))
        except OSError:
            continue
        slugs = [x["slug"] for x in bd["services"]]
        done = sum(1 for sl in slugs
                   if sl in slug_to_id and slug_to_id[sl] in touched)
        batch_cov.append({"file": b["file"], "services": len(slugs),
                          "classified": done,
                          "complete": done == len(slugs)})
    missing_batches = [b for b in batch_cov if not b["complete"]]
    if unprocessed:
        sys.stderr.write(
            f"\nWARNING: {len(unprocessed)} service(s) had integration signals but "
            f"produced neither an edge nor an unresolved signal. They were most likely "
            f"never classified (a skipped batch), NOT found to be independent:\n")
        for n in unprocessed[:25]:
            sys.stderr.write(f"  {n}\n")
        if len(unprocessed) > 25:
            sys.stderr.write(f"  ... and {len(unprocessed)-25} more\n")
    if missing_batches:
        sys.stderr.write("\nWARNING: incomplete signal batches:\n")
        for b in missing_batches:
            sys.stderr.write(f"  {b['file']}: {b['classified']}/{b['services']} "
                             f"services classified\n")
        sys.stderr.write("\nThe report is still written, but its coverage figures "
                         "understate the portfolio. Classify the missing batches, "
                         "append to edges.json, and re-run this script.\n")
    d["step4_completeness"] = {
        "batches": batch_cov,
        "incomplete_batches": [b["file"] for b in missing_batches],
        "services_with_signals_never_classified": unprocessed,
        "complete": not unprocessed and not missing_batches,
    }

    out = os.path.join(root, "interapp-dependency-analysis")
    os.makedirs(out, exist_ok=True)
    base = os.path.join(out, f"{name}-portfolio-interapp-dep-report")

    with open(base + ".json", "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)
    with open(base + ".md", "w", encoding="utf-8") as fh:
        fh.write(render_md(d, nodes))
    with open(base + ".html", "w", encoding="utf-8") as fh:
        fh.write(render_html(d, nodes))
    with open(base + ".metadata.json", "w", encoding="utf-8") as fh:
        json.dump({k: d["metadata"][k] for k in
                   ("portfolio_name", "analysis_date", "td_version",
                    "portfolio_name_source", "source_analysis_type",
                    "reports_consumed", "reports_excluded",
                    "md_enrichment_available")}
                  | {"analysis_type": "portfolio-interapp-dep"}, fh, indent=2)

    blocks = mermaid_blocks(d, nodes)
    if blocks:
        with open(base + ".diagrams.mmd", "w", encoding="utf-8") as fh:
            for title, note, src in blocks:
                fh.write(f"%% {title}\n%% {note}\n{src}\n\n")

    print(f"wrote 4 artifacts to {out}")
    for ext in ("md", "json", "html", "metadata.json", "diagrams.mmd"):
        p = base + "." + ext
        if os.path.exists(p):
            print(f"  {os.path.basename(p):<62} {os.path.getsize(p):>9,} bytes")
    sm = d["summary"]
    print(f"\n  services {sm['services_analyzed']} · app-to-app {sm['app_to_app_edges']} "
          f"· resources {sm['shared_resources']} · derived {sm['derived_pairs']} "
          f"· cycles {sm['circular_dependencies_app_to_app']} "
          f"· waves {sm['critical_path_length']} "
          f"· sequencing_valid {d['sequencing_validation']['sequencing_valid']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
