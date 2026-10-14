#!/usr/bin/env python3
"""Step 1-3 helper: collapse a MOD report tree into one compact corpus file.

Reads every per-repo MOD report under <portfolio-root>, builds the service
inventory and alias registry (SKILL.md Steps 1-2), and extracts only the
integration-relevant prose snippets (Step 3) -- discarding the ~95% of report
text that carries no dependency signal.

Output: <portfolio-root>/.iad-work/corpus.json

This exists so the analysis scales. A portfolio of a hundred repositories is a couple of hundred report files;
reading them all into one agent conversation exhausts context before any
analysis happens. This script turns them into a single file of candidate
signals that fits comfortably, while leaving every classification decision to
the agent.

Usage:  python3 -I prepare_corpus.py <portfolio-root>
Stdlib only. Python 3.8+.
"""
import sys, os, re, json, glob, collections

ROLE_SUFFIXES = ("api", "webapi", "web", "svc", "service", "services",
                 "host", "worker", "main", "soa", "app")

# Questions whose answers require describing how the app talks to other systems.
HIGH_YIELD = {"INF-Q2", "INF-Q3", "INF-Q4", "INF-Q6",
              "APP-Q2", "APP-Q3", "APP-Q6",
              "DATA-Q1", "DATA-Q2", "DATA-Q4"}

# Any mention of these in prose makes a snippet worth showing the agent.
SIGNAL_HINT = re.compile(
    r"\b(call|calls|called|invoke|invokes|consume|consumes|publish|publishes|"
    r"subscribe|subscribes|depend|depends|integrat\w*|upstream|downstream|"
    r"shared|share|shares|endpoint|endpoints|queue|topic|bus|"
    r"HTTP|REST|SOAP|WCF|gRPC|RPC|XMLHttpRequest|NetTcp|COM\+|"
    r"MSMQ|SQS|SNS|EventBridge|Kafka|RabbitMQ|ActiveMQ|Service\s*Bus|"
    r"database|catalog|schema|linked\s+server|stored\s+procedure|OLEDB|ODBC|"
    r"file\s*share|UNC|SMB|FTP|scheduler|registry|identity|SSO|LDAP)\b", re.I)

RE_UNC = re.compile(r"\\\\[A-Za-z0-9_.\-]+\\[^\s,;:)\"'`\]\\]+")
PROSE_FIELDS = ("description", "gap", "recommendation")


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def tokenize(name):
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return [t for t in re.split(r"[^A-Za-z0-9]+", name) if t]


def strip_key(key, prefixes):
    out, changed = key, True
    while changed:
        changed = False
        for p in prefixes:
            if out.startswith(p) and len(out) > len(p) + 2:
                out, changed = out[len(p):], True
        for s in ROLE_SUFFIXES:
            if out.endswith(s) and len(out) > len(s) + 2:
                out, changed = out[: -len(s)], True
    return out


def discover(root):
    """Step 1: find per-repo MOD reports at any depth; exclude portfolio rollups."""
    out, excluded = [], []
    for p in sorted(glob.glob(os.path.join(root, "**", "*-mod-report.json"),
                              recursive=True)):
        if "-portfolio-" in os.path.basename(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            excluded.append({"path": os.path.relpath(p, root),
                             "reason": f"unreadable: {exc}"})
            continue
        at = str(data.get("analysis_type", ""))
        if at and "mod" not in at.lower() and "modern" not in at.lower():
            excluded.append({"path": os.path.relpath(p, root),
                             "reason": f"analysis_type={at!r} is not a MOD type"})
            continue
        md = p[:-5] + ".md"
        meta = data.get("metadata") or {}
        slug = os.path.basename(p)[: -len("-mod-report.json")]
        out.append({
            "slug": slug,
            "repo_name": meta.get("repository") or slug,
            "repo_name_fallback": not meta.get("repository"),
            "repo_dir": os.path.basename(os.path.dirname(os.path.dirname(p))),
            "json_path": os.path.relpath(p, root),
            "md_path": os.path.relpath(md, root) if os.path.exists(md) else None,
            "md_available": os.path.exists(md),
            "overall_score": data.get("overall_score"),
            "tier": ((data.get("classification") or {}).get("tier")),
            "service_archetype": meta.get("service_archetype"),
            "repo_type": meta.get("repo_type"),
            "repository_priority": meta.get("priority"),
            "surface_flags": meta.get("surface_flags") or {},
            "_data": data, "_abs_md": md,
        })
    return out, excluded


def uniquify_slugs(inv):
    """Make every service's slug unique, qualifying duplicates by repo directory.

    Report filenames are NOT unique across a portfolio: several repos commonly
    emit 'src-mod-report.json', and the same component can appear under two repo
    directories. Left alone, duplicates are unaddressable -- edges.json refers to
    a service by slug, which resolves to exactly one node, so the second and later
    instances can never receive an edge however well they are classified, and they
    then show up as uncovered services.

    Keeps the original slug as an alias so prose matching still works.
    """
    counts = collections.Counter(r["slug"] for r in inv)
    renamed = []
    for r in inv:
        r["slug_original"] = r["slug"]
        if counts[r["slug"]] > 1:
            r["slug"] = f"{r['slug']}--{re.sub(r'[^A-Za-z0-9]+', '-', r['repo_dir']).strip('-').lower()}"
            renamed.append({"original": r["slug_original"], "qualified": r["slug"],
                            "repo_dir": r["repo_dir"]})
    # A qualified slug could still collide in pathological layouts; append an index.
    seen = collections.Counter()
    for r in inv:
        seen[r["slug"]] += 1
        if seen[r["slug"]] > 1:
            r["slug"] = f"{r['slug']}-{seen[r['slug']]}"
    return renamed


def derive_prefixes(inv, min_repos=3):
    """Step 2.2: organization/system prefixes = leading tokens shared by 3+ entries."""
    c = collections.Counter()
    for r in inv:
        for field in ("repo_name", "repo_dir", "slug"):
            toks = tokenize(r[field])
            if toks:
                c[toks[0].lower()] += 1
    return sorted({t for t, n in c.items() if n >= min_repos and len(t) >= 3})


def build_registry(inv, prefixes):
    """Step 2: alias registry with exact + stripped match keys and collisions."""
    exact = collections.defaultdict(set)
    stripped = collections.defaultdict(set)
    per_repo_aliases = {}

    for r in inv:
        aliases = {r["repo_name"], r["repo_dir"], r["slug"],
                   r.get("slug_original") or r["slug"]}
        for f in r["_data"].get("findings", []):
            ev = ((f.get("evidence") or {}).get("file")) or ""
            for seg in str(ev).split("/"):
                seg = re.sub(r"\.(csproj|sln|cs|vb|java|config|json|yml|yaml|asp|aspx)$",
                             "", seg)
                if "." in seg and seg[:1].isupper():
                    aliases.add(seg)
        aliases = {a for a in aliases if a}
        per_repo_aliases[r["slug"]] = sorted(aliases)
        for a in aliases:
            k = norm(a)
            if len(k) >= 5:
                exact[k].add(r["slug"])
                sk = strip_key(k, prefixes)
                if len(sk) >= 4:
                    stripped[sk].add(r["slug"])

    collisions = []
    for bucket, kind in ((exact, "exact"), (stripped, "stripped")):
        for k, v in bucket.items():
            if len(v) > 1:
                collisions.append({"match_key": k, "kind": kind,
                                   "competing_services": sorted(v)})
    return ({k: next(iter(v)) for k, v in exact.items() if len(v) == 1},
            {k: next(iter(v)) for k, v in stripped.items() if len(v) == 1},
            collisions, per_repo_aliases)


def md_blocks(path):
    """Parse per-repo MD into {question_id: [row text, ...]} for the signal rows."""
    out = collections.defaultdict(list)
    try:
        md = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return out
    for m in re.finditer(r"^#### ([A-Z]+-Q\d+):.*?$(.*?)(?=^#### |\Z)", md, re.M | re.S):
        qid, block = m.group(1), m.group(2)
        for row in re.finditer(
                r"\|\s*\*\*(Finding|Gap|Evidence)\*\*\s*\|(.*?)\|\s*$", block, re.M):
            out[qid].append(row.group(2).strip())
    return out


def snippets_for(rep):
    """Step 3: integration-relevant prose only. JSON primary, MD enrichment."""
    seen, out = set(), []

    def add(text, qid, artifact):
        if not text:
            return
        text = re.sub(r"\s+", " ", str(text)).strip()
        if len(text) < 25 or not SIGNAL_HINT.search(text):
            return
        key = (qid, text[:160])
        if key in seen:
            return
        seen.add(key)
        out.append({"question_id": qid, "artifact": artifact, "text": text[:700]})

    for f in rep["_data"].get("findings", []):
        qid = f.get("question_id", "?")
        for fld in PROSE_FIELDS:
            # recommendations describe systems that do not exist; only mine them
            # on high-yield questions, where they can corroborate a peer name.
            if fld == "recommendation" and qid not in HIGH_YIELD:
                continue
            add(f.get(fld), qid, "json")
        ev = (f.get("evidence") or {}).get("file")
        if ev and (RE_UNC.search(str(ev)) or qid in HIGH_YIELD):
            add(f"EVIDENCE FILE: {ev}", qid, "json")

    for g in rep["_data"].get("top_gaps", []):
        add(g.get("gap"), g.get("question_id", "TOPGAP"), "json")
        add(g.get("impact"), g.get("question_id", "TOPGAP"), "json")

    ds = rep["_data"].get("decomposition_strategy") or {}
    for k, v in (ds.get("effort_factors") or {}).items():
        if k in ("data_coupling", "communication_patterns"):
            add(v, f"DECOMP:{k}", "json")

    add((rep["_data"].get("metadata") or {}).get("archetype_justification"),
        "META:archetype", "json")

    if rep["md_available"]:
        for qid, rows in md_blocks(rep["_abs_md"]).items():
            if qid in HIGH_YIELD:
                for row in rows:
                    add(row, qid, "md")
    return out


def main():
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    root = os.path.abspath(sys.argv[1])
    inv, excluded = discover(root)

    if len(inv) < 2:
        sys.stderr.write(
            f"\nFATAL: Inter-app dependency analysis requires at least 2 per-repo "
            f"MOD reports; found {len(inv)} under {root}. Run the Modernization "
            f"Readiness Analysis across the portfolio first.\n")
        return 1

    renamed = uniquify_slugs(inv)
    prefixes = derive_prefixes(inv)
    exact, stripped, collisions, aliases = build_registry(inv, prefixes)

    services, batches, total_snips = [], [], 0
    cur, cur_bytes = [], 0
    BATCH_BYTES = 110_000      # keeps each batch file comfortably readable

    for r in inv:
        snips = snippets_for(r)
        total_snips += len(snips)
        services.append({
            "slug": r["slug"], "repo_name": r["repo_name"],
            "repo_dir": r["repo_dir"],
            "json_path": r["json_path"], "md_path": r["md_path"],
            "md_available": r["md_available"],
            "overall_score": r["overall_score"], "tier": r["tier"],
            "service_archetype": r["service_archetype"],
            "repo_type": r["repo_type"],
            "repository_priority": r["repository_priority"],
            "surface_flags": r["surface_flags"],
            "aliases": aliases[r["slug"]],
            "signal_count": len(snips),
        })
        entry = {"slug": r["slug"], "repo_name": r["repo_name"],
                 "aliases": aliases[r["slug"]], "signal_snippets": snips}
        sz = len(json.dumps(entry))
        if cur and cur_bytes + sz > BATCH_BYTES:
            batches.append(cur); cur, cur_bytes = [], 0
        cur.append(entry); cur_bytes += sz
    if cur:
        batches.append(cur)

    work = os.path.join(root, ".iad-work")
    os.makedirs(work, exist_ok=True)
    sig_dir = os.path.join(work, "signals")
    os.makedirs(sig_dir, exist_ok=True)
    for old in glob.glob(os.path.join(sig_dir, "batch-*.json")):
        os.remove(old)

    # Clear classification output from any previous run. A stale edges.json or
    # working-edges.jsonl silently mixes a previous run's conclusions into this
    # one -- including conclusions drawn from different reports or different
    # extraction rules. Preserve them under .prev so nothing is destroyed.
    for stale in ("edges.json", "working-edges.jsonl"):
        p = os.path.join(work, stale)
        if os.path.exists(p):
            prev = os.path.join(work, "prev")
            os.makedirs(prev, exist_ok=True)
            os.replace(p, os.path.join(prev, stale))
            print(f"  note: moved stale {stale} to .iad-work/prev/{stale}")

    batch_files = []
    for n, b in enumerate(batches, 1):
        fn = f"batch-{n:03d}.json"
        with open(os.path.join(sig_dir, fn), "w", encoding="utf-8") as fh:
            json.dump({"batch": n, "of": len(batches), "services": b}, fh, indent=1)
        batch_files.append({"file": f"signals/{fn}", "services": len(b),
                            "snippets": sum(len(x["signal_snippets"]) for x in b)})

    corpus = {
        "schema": "iad-corpus-1",
        "portfolio_root": root,
        "portfolio_dir_name": os.path.basename(root),
        "counts": {
            "services": len(services),
            "excluded_reports": len(excluded),
            "md_available": sum(1 for s in services if s["md_available"]),
            "signal_snippets": total_snips,
            "services_with_no_signals":
                sum(1 for s in services if not s["signal_count"]),
            "batches": len(batches),
        },
        "duplicate_slugs_qualified": renamed,
        "derived_naming_prefixes": prefixes,
        "match_keys": {"exact": exact, "stripped": stripped},
        "alias_collisions": collisions,
        "excluded_reports": excluded,
        "signal_batches": batch_files,
        "services": services,
    }

    out_path = os.path.join(work, "corpus.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(corpus, fh, indent=1)

    c = corpus["counts"]
    print(f"corpus written: {out_path}  ({os.path.getsize(out_path):,} bytes)")
    print(f"  services                 : {c['services']}")
    print(f"  markdown available       : {c['md_available']}")
    print(f"  signal snippets          : {c['signal_snippets']}")
    print(f"  services with no signals : {c['services_with_no_signals']}")
    print(f"  excluded reports         : {c['excluded_reports']}")
    print(f"  derived prefixes         : {prefixes}")
    print(f"  exact match keys         : {len(exact)}")
    print(f"  stripped match keys      : {len(stripped)}")
    print(f"  alias collisions         : {len(collisions)}")
    if renamed:
        print(f"  duplicate slugs qualified: {len(renamed)}")
        for r in renamed[:8]:
            print(f"    {r['original']} -> {r['qualified']}")
    print(f"\n  signal batches to review : {c['batches']}")
    for b in batch_files:
        print(f"    {b['file']:<28} {b['services']:>3} services  "
              f"{b['snippets']:>4} snippets")
    print("\nNext: read corpus.json, then each signals/batch-*.json in turn, "
          "classify edges, write .iad-work/edges.json, then run render_report.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
