#!/usr/bin/env python3
"""
Agentic Readiness Dashboard Generator

Parses a portfolio agentic readiness assessment markdown report and generates
an interactive CAST-style HTML dashboard for Decision Makers and SAs.

Usage:
    python generate_dashboard.py <report.md> [-o output.html]

Example:
    python generate_dashboard.py ../agentic-readiness-assessment/ecommerce-platform-test-portfolio-agentic-readiness-report.md
"""

import re, json, sys, argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ServiceScore:
    name: str
    score: float
    priority: str = "P0"
    categories: dict = field(default_factory=dict)

@dataclass
class CategoryScore:
    name: str
    score: float
    status: str = ""

@dataclass
class Gap:
    id: str
    title: str
    score: str
    affected: int
    impact: str = ""
    recommendation: str = ""
    is_blocking: bool = False

@dataclass
class Phase:
    name: str
    timeframe: str
    objective: str
    effort: str = "High"

@dataclass
class Dep:
    source: str
    target: str
    dtype: str

@dataclass
class Pathway:
    name: str
    services_triggered: int
    total_services: int
    priority: str = "High"
    effort: str = "High"
    per_service: dict = field(default_factory=dict)  # service_name -> bool

@dataclass
class QuickWin:
    title: str
    repos: str
    description: str

@dataclass
class Portfolio:
    name: str = ""
    goal: str = ""
    goal_context: str = ""
    date: str = ""
    total_services: int = 0
    score: float = 0.0
    services: List[ServiceScore] = field(default_factory=list)
    categories: List[CategoryScore] = field(default_factory=list)
    blocking_gaps: List[Gap] = field(default_factory=list)
    general_gaps: List[Gap] = field(default_factory=list)
    phases: List[Phase] = field(default_factory=list)
    deps: List[Dep] = field(default_factory=list)
    pathways: List[Pathway] = field(default_factory=list)
    quick_wins: List[QuickWin] = field(default_factory=list)
    summary: str = ""
    strengths: list = field(default_factory=list)
    common_gaps: list = field(default_factory=list)


# ── Parser ───────────────────────────────────────────────────────────────────

def get_section(content: str, heading: str) -> Optional[str]:
    """Extract content under a heading, stopping at the next heading of same or higher level."""
    # Try ### heading first (most specific)
    pat3 = rf'(?:^|\n)###\s*{re.escape(heading)}\s*\n(.*?)(?=\n###\s|\n##[^#]|\n---|\Z)'
    m3 = re.search(pat3, content, re.DOTALL)
    if m3: return m3.group(1)
    # Try ## heading
    pat2 = rf'(?:^|\n)##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\n---|\Z)'
    m2 = re.search(pat2, content, re.DOTALL)
    if m2: return m2.group(1)
    # Fallback: any heading level, stop at same or higher
    pat = rf'{re.escape(heading)}\s*\n(.*?)(?=\n##|\n---|\Z)'
    m = re.search(pat, content, re.DOTALL)
    return m.group(1) if m else None


def parse_report(content: str) -> Portfolio:
    d = Portfolio()

    # Header metadata
    for key, attr in [("Portfolio", "name"), ("Assessment Goal", "goal"),
                      ("Goal Context", "goal_context"), ("Assessment Date", "date")]:
        m = re.search(rf'\*\*{key}\*\*:\s*(.+)', content)
        if m: setattr(d, attr, m.group(1).strip())

    m = re.search(r'\*\*Services Assessed\*\*:\s*(\d+)', content)
    if m: d.total_services = int(m.group(1))

    m = re.search(r'Portfolio Readiness Score:\s*([\d.]+)\s*/\s*4\.0', content)
    if m: d.score = float(m.group(1))

    # Executive summary
    sec = get_section(content, "Executive Dashboard")
    if sec:
        paras = [p.strip() for p in sec.split('\n\n')
                 if p.strip() and not p.strip().startswith(('#','|','---','*'))]
        if paras: d.summary = paras[0]

    # Categories from table
    cats = re.findall(
        r'\|\s*(Infrastructure[^|]*|Application[^|]*|Data[^|]*|Identity[^|]*|Operations[^|]*)\s*\|\s*([\d.]+)\s*/\s*4\.0\s*\|[^|]*\|\s*([^\|]+)\|',
        content)
    for name, score, status in cats:
        d.categories.append(CategoryScore(name.strip(), float(score), status.strip()))

    # Services from readiness distribution — match "service-name (1.8)" patterns
    # Use broader unicode-aware dash matching and search more of the document
    svcs = re.findall(r'[\u2014\u2013\-]\s*([\w][\w-]+)\s*\(([\d.]+)\)', content[:5000])
    # Also try comma-separated: "svc1 (1.8), svc2 (2.1)"
    svcs += re.findall(r',\s*([\w][\w-]+)\s*\(([\d.]+)\)', content[:5000])
    seen = set()
    for name, score in svcs:
        # Filter out non-service matches
        if name in seen or len(name) < 4 or name in ('services','service'):
            continue
        try:
            sc_val = float(score)
            if sc_val > 4.0 or sc_val < 0: continue
        except ValueError:
            continue
        # Validate: name must appear in a table row (|name|) or dependency section
        if not re.search(rf'\|\s*{re.escape(name)}\s', content):
            continue
        seen.add(name)
        s = ServiceScore(name=name, score=sc_val)
        pm = re.search(rf'{re.escape(name)}.*?(P[012])', content)
        if pm: s.priority = pm.group(1)
        d.services.append(s)

    # Per-service category scores from per-category analysis
    cat_shorts = {"Infrastructure": "INF", "Application": "APP",
                  "Data": "DATA", "Identity": "SEC", "Operations": "OPS"}
    for svc in d.services:
        for cat in d.categories:
            short = next((v for k, v in cat_shorts.items() if k in cat.name), cat.name[:3].upper())
            sec2 = get_section(content, cat.name)
            if sec2:
                pm2 = re.search(rf'{re.escape(svc.name)}[^)]*?\(?([\d.]+)/4\.0', sec2)
                if pm2:
                    svc.categories[short] = float(pm2.group(1))
        if not svc.categories:
            for cat in d.categories:
                short = next((v for k, v in cat_shorts.items() if k in cat.name), cat.name[:3].upper())
                svc.categories[short] = cat.score

    # Cross-cutting gaps
    def parse_gaps(sec_name, blocking):
        sec3 = get_section(content, sec_name)
        if not sec3: return
        gps = re.findall(
            r'\d+\.\s*\*\*(\w+-\w+):\s*([^*]+)\*\*\s*[\u2014\u2013\-]+\s*(\d+)\s*of\s*(\d+)\s*services?\s*score\s*([^\n]+)',
            sec3)
        for gid, title, aff, tot, sc in gps:
            g = Gap(gid.strip(), title.strip(), sc.strip(), int(aff), is_blocking=blocking)
            im = re.search(rf'{re.escape(gid)}.*?\*\*Impact[^:]*:\*\*\s*([^\n]+)', sec3)
            if im: g.impact = im.group(1).strip()
            rec = re.search(rf'{re.escape(gid)}.*?\*\*Recommend[^:]*:\*\*\s*([^\n]+)', sec3)
            if rec: g.recommendation = rec.group(1).strip()
            if blocking: d.blocking_gaps.append(g)
            else: d.general_gaps.append(g)

    parse_gaps("Blocking Your Goal", True)
    parse_gaps("General Opportunities", False)

    # Dependencies
    dep_sec = get_section(content, "Service Dependency Map")
    if dep_sec:
        seen_deps = set()
        for m in re.finditer(r'([\w-]+)\s*→\s*([\w-]+).*?(sync|async|SYNC|ASYNC|REST|EventBridge)', dep_sec):
            dt = "sync" if any(x in m.group(3).lower() for x in ["sync","rest"]) else "async"
            key = (m.group(1), m.group(2), dt)
            if key not in seen_deps:
                seen_deps.add(key)
                d.deps.append(Dep(m.group(1), m.group(2), dt))

    # Roadmap phases
    rmap = get_section(content, "Portfolio Modernization Roadmap")
    if rmap:
        for m in re.finditer(r'###\s*Phase\s*(\d+)\s*[—–-]\s*([^(]+)\(([^)]+)\)\s*\n\n\*\*Objective\*\*:\s*([^\n]+)', rmap):
            d.phases.append(Phase(f"Phase {m.group(1)} — {m.group(2).strip()}", m.group(3).strip(), m.group(4).strip()))

    # Strengths and common gaps
    ss = get_section(content, "Common Strengths")
    if ss: d.strengths = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', ss)
    gs = get_section(content, "Common Gaps")
    if gs: d.common_gaps = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', gs)

    # Modernization Pathways
    pw_sec = get_section(content, "AWS Modernization Pathways")
    if pw_sec:
        # Parse pathway summary table
        pw_rows = re.findall(
            r'\|\s*(Move to [^|]+?)\s*\|\s*(\d+)\s*services?\s*\|\s*(\d+)%[^|]*\|\s*(\w+)\s*\|\s*([^\|]*?)\s*\|',
            pw_sec)
        svc_names = [s.name for s in d.services]
        n_svc = d.total_services or len(d.services)
        for pname, triggered, pct_val, priority, effort in pw_rows:
            pw = Pathway(name=pname.strip(), services_triggered=int(triggered),
                         total_services=n_svc, priority=priority.strip(),
                         effort=effort.strip().rstrip('—').strip() or "N/A")
            d.pathways.append(pw)

        # Parse per-service pathway assignment table
        # Find the specific sub-section
        assign_start = pw_sec.find('Per-Service Pathway Assignment')
        if assign_start >= 0 and d.pathways:
            assign_chunk = pw_sec[assign_start:assign_start+1500]
            header_m = re.search(r'\|\s*Service\s*\|([^\n]+)', assign_chunk)
            if header_m:
                col_names = [h.strip() for h in header_m.group(1).split('|') if h.strip()]
                # Map columns to pathways by fuzzy matching short names
                col_to_pw = {}
                # Normalize abbreviations
                abbrevs = {'db': 'databases', 'devops': 'devops', 'ai': 'ai'}
                def normalize(s):
                    words = s.split()
                    return ' '.join(abbrevs.get(w, w) for w in words)
                for ci, col in enumerate(col_names):
                    col_lower = normalize(col.lower().replace('move to ', '').strip())
                    best_pw = None
                    best_score = 0
                    for pw in d.pathways:
                        pw_short = normalize(pw.name.lower().replace('move to ', '').strip())
                        # Exact match
                        if col_lower == pw_short:
                            best_pw = pw; best_score = 100; break
                        # Column is abbreviation of pathway (e.g. "managed db" in "managed databases")
                        if pw_short.startswith(col_lower):
                            score = len(col_lower)
                            if score > best_score: best_pw = pw; best_score = score
                        # Pathway short is substring of column
                        elif col_lower.startswith(pw_short):
                            score = len(pw_short)
                            if score > best_score: best_pw = pw; best_score = score
                        # Word-level match (all words in col appear in pw)
                        else:
                            col_words = col_lower.split()
                            pw_words = pw_short.split()
                            # Check if each col word is a prefix of some pw word
                            if col_words and all(
                                any(pww.startswith(cw) for pww in pw_words) for cw in col_words
                            ):
                                score = len(col_lower)
                                if score > best_score: best_pw = pw; best_score = score
                    if best_pw:
                        col_to_pw[ci] = best_pw
                # Parse each service row from this specific table chunk
                for svc in d.services:
                    row_m = re.search(rf'\|\s*{re.escape(svc.name)}\s*\|([^\n]+)', assign_chunk)
                    if row_m:
                        raw_cells = row_m.group(1).split('|')
                        for ci, pw in col_to_pw.items():
                            if ci < len(raw_cells):
                                cell = raw_cells[ci].strip()
                                pw.per_service[svc.name] = cell in ('✅', 'Yes', 'yes', '✓')

    # Quick Agent Wins
    qw_sec = get_section(content, "Portfolio Quick Agent Wins")
    if qw_sec:
        # Parse bold title blocks: **Title** (N repos: repo1, repo2)
        qw_blocks = re.split(r'\n\*\*(?=[A-Z])', qw_sec)
        for block in qw_blocks:
            tm = re.match(r'([^*]+)\*\*\s*\((\d+\s*repos?:[^)]+)\)', block)
            if tm:
                title = tm.group(1).strip()
                repos = tm.group(2).strip()
                desc_text = block[tm.end():].strip()
                # Clean up description: take first paragraph
                desc_lines = []
                for line in desc_text.split('\n'):
                    line = line.strip().lstrip('- ')
                    if not line or line.startswith('**'):
                        break
                    desc_lines.append(line)
                desc = ' '.join(desc_lines)[:300]
                d.quick_wins.append(QuickWin(title=title, repos=repos, description=desc))

    return d


# ── HTML Generator ───────────────────────────────────────────────────────────

def sc(score):
    """Score to CSS color var name."""
    if score >= 3.5: return "var(--green)"
    if score >= 2.5: return "var(--yellow)"
    if score >= 1.5: return "var(--orange)"
    return "var(--red)"

def tier(score):
    if score >= 3.5: return "Agent-Ready"
    if score >= 2.5: return "Partial"
    if score >= 1.5: return "Needs Work"
    return "Not Ready"

def emoji(score):
    if score >= 3.5: return "✅"
    if score >= 2.5: return "🟡"
    if score >= 1.5: return "🟠"
    return "❌"

def pct(score, mx=4.0):
    return min(100, max(0, (score / mx) * 100))


def generate_html(d: Portfolio) -> str:
    nr = sum(1 for s in d.services if s.score < 1.5)
    nw = sum(1 for s in d.services if 1.5 <= s.score < 2.5)
    pa = sum(1 for s in d.services if 2.5 <= s.score < 3.5)
    ar = sum(1 for s in d.services if s.score >= 3.5)
    n = d.total_services or len(d.services)

    svc_j = json.dumps([{"name":s.name,"score":s.score,"priority":s.priority,"categories":s.categories} for s in d.services])
    cat_j = json.dumps([{"name":c.name,"score":c.score} for c in d.categories])
    bg_j = json.dumps([{"id":g.id,"title":g.title,"score":g.score,"affected":g.affected,"impact":g.impact,"rec":g.recommendation} for g in d.blocking_gaps])
    gg_j = json.dumps([{"id":g.id,"title":g.title,"score":g.score,"affected":g.affected,"impact":g.impact,"rec":g.recommendation} for g in d.general_gaps])
    dep_j = json.dumps([{"source":x.source,"target":x.target,"type":x.dtype} for x in d.deps])
    ph_j = json.dumps([{"name":p.name,"timeframe":p.timeframe,"objective":p.objective} for p in d.phases])
    pw_j = json.dumps([{"name":pw.name,"triggered":pw.services_triggered,"total":pw.total_services,
                         "priority":pw.priority,"effort":pw.effort,"perService":pw.per_service} for pw in d.pathways])
    qw_j = json.dumps([{"title":q.title,"repos":q.repos,"description":q.description} for q in d.quick_wins])
    str_j = json.dumps(d.strengths)
    cgap_j = json.dumps(d.common_gaps)
    summ = d.summary.replace("**","").replace("'","\\'").replace("\n"," ").replace('"','\\"').replace('\u2014','-').replace('\u2013','-')

    return _html(d, nr, nw, pa, ar, n, svc_j, cat_j, bg_j, gg_j, dep_j, ph_j, pw_j, qw_j, str_j, cgap_j, summ)


def _html(d, nr, nw, pa, ar, n, svc_j, cat_j, bg_j, gg_j, dep_j, ph_j, pw_j, qw_j, str_j, cgap_j, summ):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agentic Readiness — {d.name}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
''' + CSS_BLOCK + f'''
</head>
<body>
<div class="bg-glow"></div>
<div class="container">

<div class="header">
  <div class="badge">AWS Transform — Agentic Readiness Assessment</div>
  <h1>{d.name}</h1>
  <div class="subtitle">Portfolio Assessment · {n} Services · {d.date}</div>
  <div class="goal-ctx">Goal: {d.goal} — {d.goal_context}</div>
</div>

<div class="nav">
  <button class="nav-btn active" onclick="showSection('overview',this)">Overview</button>
  <button class="nav-btn" onclick="showSection('services',this)">Services</button>
  <button class="nav-btn" onclick="showSection('categories',this)">Categories</button>
  <button class="nav-btn" onclick="showSection('gaps',this)">Risks & Gaps</button>
  <button class="nav-btn" onclick="showSection('pathways',this)">Pathways</button>
  <button class="nav-btn" onclick="showSection('dependencies',this)">Dependencies</button>
  <button class="nav-btn" onclick="showSection('roadmap',this)">Roadmap</button>
</div>

<!-- OVERVIEW -->
<div id="sec-overview" class="section active">
  <div class="score-hero">
    <div class="score-ring-wrap">
      <canvas id="scoreRing"></canvas>
      <div class="score-center">
        <div class="num" id="heroScore">0</div>
        <div class="label">of 4.0</div>
      </div>
    </div>
    <div class="score-meta">
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--red)"></div><div class="score-meta-text"><strong>{nr} service{"s" if nr!=1 else ""}</strong> — Not Ready (&lt;1.5)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--orange)"></div><div class="score-meta-text"><strong>{nw} service{"s" if nw!=1 else ""}</strong> — Needs Work (1.5–2.4)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--yellow)"></div><div class="score-meta-text"><strong>{pa} service{"s" if pa!=1 else ""}</strong> — Partial (2.5–3.4)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--green)"></div><div class="score-meta-text"><strong>{ar} service{"s" if ar!=1 else ""}</strong> — Agent-Ready (3.5–4.0)</div></div>
    </div>
  </div>

  <div class="exec-summary card" style="margin-bottom:24px">
    <div class="card-title">Executive Summary</div>
    <p style="font-size:14px;line-height:1.7;color:var(--text2)" id="execSummary"></p>
  </div>

  <div class="grid grid-4" style="margin-bottom:24px">
    <div class="card"><div class="card-title">Services Assessed</div><div class="card-value" style="color:var(--accent2)">{n}</div></div>
    <div class="card"><div class="card-title">Agent-Ready</div><div class="card-value" style="color:{sc(4.0) if ar>0 else sc(0)}">{round(ar/max(n,1)*100)}%</div><div class="card-sub">{ar} of {n} services</div></div>
    <div class="card"><div class="card-title">Blocking Gaps</div><div class="card-value" style="color:var(--red)">{len(d.blocking_gaps)}</div><div class="card-sub">Cross-cutting blockers</div></div>
    <div class="card"><div class="card-title">Roadmap Phases</div><div class="card-value" style="color:var(--accent2)">{len(d.phases)}</div><div class="card-sub">{"→".join(p.timeframe for p in d.phases) if d.phases else "N/A"}</div></div>
  </div>

  <div class="card" style="margin-bottom:24px">
    <div class="card-title">Category Readiness</div>
    <div id="catBars"></div>
  </div>

  <div class="grid grid-2">
    <div class="card"><div class="card-title">Strengths</div><ul id="strengthsList" style="list-style:none;padding:0"></ul></div>
    <div class="card"><div class="card-title">Common Gaps</div><ul id="gapsList" style="list-style:none;padding:0"></ul></div>
  </div>

  <div class="card" style="margin-top:24px" id="quickWinsCard">
    <div class="card-title">⚡ Quick Agent Wins</div>
    <div id="quickWinsList" class="grid grid-2" style="gap:16px"></div>
  </div>
</div>

<!-- SERVICES -->
<div id="sec-services" class="section">
  <div class="grid grid-2" id="serviceCards"></div>
</div>

<!-- CATEGORIES -->
<div id="sec-categories" class="section">
  <div class="card" style="margin-bottom:24px">
    <div class="card-title">Category Comparison — Radar</div>
    <canvas id="radarChart" height="400"></canvas>
  </div>
  <div class="card">
    <div class="card-title">Heatmap — Score by Service × Category</div>
    <canvas id="heatmapChart" height="280"></canvas>
  </div>
</div>

<!-- GAPS -->
<div id="sec-gaps" class="section">
  <div class="card" style="margin-bottom:24px">
    <div class="card-title">🚫 Blocking Your Goal ({len(d.blocking_gaps)} gaps)</div>
    <table class="gap-table"><thead><tr><th>ID</th><th>Gap</th><th>Score</th><th>Services</th><th>Impact</th></tr></thead>
    <tbody id="blockingTable"></tbody></table>
  </div>
  <div class="card">
    <div class="card-title">⚡ General Opportunities ({len(d.general_gaps)} gaps)</div>
    <table class="gap-table"><thead><tr><th>ID</th><th>Gap</th><th>Score</th><th>Services</th><th>Impact</th></tr></thead>
    <tbody id="generalTable"></tbody></table>
  </div>
</div>

<!-- PATHWAYS -->
<div id="sec-pathways" class="section">
  <div style="text-align:center;margin-bottom:32px">
    <h2 style="font-size:28px;font-weight:800;margin-bottom:8px">AWS Modernization Pathways</h2>
    <p style="color:var(--text2);font-size:14px">Pathway coverage across the portfolio</p>
  </div>
  <div class="card" style="margin-bottom:24px">
    <div class="card-title">Pathway Coverage</div>
    <canvas id="pathwayChart" height="280"></canvas>
  </div>
  <div id="pathwayCards" class="grid grid-3" style="margin-bottom:24px"></div>
  <div class="card">
    <div class="card-title">Pathway × Service Matrix</div>
    <div id="pathwayMatrix" style="overflow-x:auto"></div>
  </div>
</div>

<!-- DEPENDENCIES -->
<div id="sec-dependencies" class="section">
  <div class="dep-graph">
    <div class="card-title" style="margin-bottom:24px">Service Dependency Architecture</div>
    <div id="depViz" style="min-height:300px"></div>
  </div>
  <div class="card">
    <div class="card-title">Dependency Matrix</div>
    <table class="gap-table"><thead><tr><th>Source → Target</th><th>Type</th><th>Risk</th></tr></thead>
    <tbody id="depTable"></tbody></table>
  </div>
</div>

<!-- ROADMAP -->
<div id="sec-roadmap" class="section">
  <div style="text-align:center;margin-bottom:32px">
    <h2 style="font-size:28px;font-weight:800;margin-bottom:8px">Modernization Roadmap</h2>
    <p style="color:var(--text2);font-size:14px">{len(d.phases)} phases</p>
  </div>
  <div class="card" style="margin-bottom:24px">
    <div class="card-title">Phase Timeline</div>
    <canvas id="ganttChart" height="180"></canvas>
  </div>
  <div id="phaseCards" class="grid grid-2"></div>
</div>

<!-- DETAIL OVERLAY -->
<div class="detail-overlay" id="detailOverlay" onclick="if(event.target===this)closeDetail()">
  <div class="detail-panel" id="detailPanel"></div>
</div>

</div>''' + f'''
<script>
// ── Data ──
const DATA = {{
  name: "{d.name}",
  score: {d.score},
  services: {svc_j},
  categories: {cat_j},
  blocking: {bg_j},
  general: {gg_j},
  deps: {dep_j},
  phases: {ph_j},
  pathways: {pw_j},
  quickWins: {qw_j},
  strengths: {str_j},
  commonGaps: {cgap_j},
  summary: "{summ}"
}};
''' + JS_BLOCK + '''
</script>
</body>
</html>'''


# ── CSS ──────────────────────────────────────────────────────────────────────
CSS_BLOCK = '''<style>
:root{--bg:#0f1117;--surface:#1a1d27;--surface2:#232733;--border:#2d3140;--text:#e4e6f0;--text2:#9ca0b0;--accent:#6c5ce7;--accent2:#a29bfe;--green:#00cec9;--yellow:#fdcb6e;--orange:#e17055;--red:#d63031;--blue:#0984e3;--teal:#00b894;--radius:16px;--shadow:0 8px 32px rgba(0,0,0,.4)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);overflow-x:hidden}
.bg-glow{position:fixed;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle at 30% 40%,rgba(108,92,231,.08) 0%,transparent 50%),radial-gradient(circle at 70% 60%,rgba(0,206,201,.06) 0%,transparent 50%);animation:bgFloat 20s ease-in-out infinite;z-index:0;pointer-events:none}
@keyframes bgFloat{0%,100%{transform:translate(0,0)}50%{transform:translate(-2%,2%)}}
.container{max-width:1440px;margin:0 auto;padding:24px 32px;position:relative;z-index:1}
.header{text-align:center;padding:48px 0 24px}
.header .badge{display:inline-block;background:linear-gradient(135deg,var(--accent),var(--blue));padding:6px 16px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:16px}
.header h1{font-size:42px;font-weight:800;background:linear-gradient(135deg,var(--text),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.header .subtitle{color:var(--text2);font-size:15px}
.header .goal-ctx{color:var(--accent2);font-size:13px;margin-top:8px;font-style:italic}
.nav{display:flex;justify-content:center;gap:8px;margin:24px 0;flex-wrap:wrap}
.nav-btn{background:var(--surface);border:1px solid var(--border);color:var(--text2);padding:10px 20px;border-radius:10px;cursor:pointer;font-size:13px;font-weight:500;transition:all .25s}
.nav-btn:hover,.nav-btn.active{background:var(--accent);color:#fff;border-color:var(--accent);transform:translateY(-1px)}
.section{display:none;animation:fadeIn .4s ease}.section.active{display:block}
@keyframes fadeIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
</style>
'''

CSS_BLOCK += '''<style>
.score-hero{display:flex;align-items:center;justify-content:center;gap:64px;padding:40px 0;flex-wrap:wrap}
.score-ring-wrap{position:relative;width:220px;height:220px}
.score-ring-wrap canvas{width:220px!important;height:220px!important}
.score-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center}
.score-center .num{font-size:48px;font-weight:800}.score-center .label{font-size:13px;color:var(--text2);margin-top:2px}
.score-meta{display:flex;flex-direction:column;gap:14px}
.score-meta-item{display:flex;align-items:center;gap:12px}
.score-meta-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.score-meta-text{font-size:14px;color:var(--text2)}.score-meta-text strong{color:var(--text);font-weight:600}
.grid{display:grid;gap:20px}
.grid-2{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}
.grid-3{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.grid-4{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:24px;transition:all .3s}
.card:hover{border-color:var(--accent);box-shadow:var(--shadow),0 0 20px rgba(108,92,231,.1);transform:translateY(-2px)}
.card-title{font-size:13px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:1px;margin-bottom:16px}
.card-value{font-size:32px;font-weight:800}.card-sub{font-size:12px;color:var(--text2);margin-top:4px}
.svc-card{cursor:pointer;position:relative;overflow:hidden}
.svc-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:var(--radius) var(--radius) 0 0}
.svc-card.tier-red::before{background:var(--red)}.svc-card.tier-orange::before{background:var(--orange)}
.svc-card.tier-yellow::before{background:var(--yellow)}.svc-card.tier-green::before{background:var(--green)}
.svc-name{font-size:16px;font-weight:700;margin-bottom:4px}
.svc-score{font-size:36px;font-weight:800;margin-bottom:4px}
.svc-bar-row{display:flex;align-items:center;gap:8px;margin:6px 0}
.svc-bar-label{font-size:11px;color:var(--text2);width:80px;flex-shrink:0}
.svc-bar-track{flex:1;height:6px;background:var(--surface2);border-radius:3px;overflow:hidden}
.svc-bar-fill{height:100%;border-radius:3px;transition:width 1s ease}
.svc-priority{display:inline-block;padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700;margin-top:12px}
.svc-priority.p0{background:rgba(214,48,49,.15);color:var(--red)}.svc-priority.p1{background:rgba(253,203,110,.15);color:var(--yellow)}
.cat-row{display:flex;align-items:center;gap:16px;padding:14px 0;border-bottom:1px solid var(--border)}
.cat-row:last-child{border-bottom:none}
.cat-label{width:220px;font-size:14px;font-weight:500;flex-shrink:0}
.cat-bar-wrap{flex:1;display:flex;align-items:center;gap:12px}
.cat-bar-track{flex:1;height:12px;background:var(--surface2);border-radius:6px;overflow:hidden}
.cat-bar-fill{height:100%;border-radius:6px;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.cat-score{font-size:14px;font-weight:700;width:60px;text-align:right;flex-shrink:0}
.cat-status{font-size:16px;width:24px;text-align:center;flex-shrink:0}
</style>
'''

CSS_BLOCK += '''<style>
.gap-table{width:100%;border-collapse:collapse}
.gap-table th{text-align:left;padding:12px 16px;font-size:12px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid var(--border)}
.gap-table td{padding:12px 16px;font-size:13px;border-bottom:1px solid var(--border)}
.gap-table tr:hover td{background:var(--surface2)}
.gap-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.dep-graph{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:32px;margin:24px 0}
.dep-node{background:var(--surface2);border:2px solid var(--border);border-radius:12px;padding:16px 20px;text-align:center;display:inline-block;margin:8px;transition:all .3s}
.dep-node:hover{border-color:var(--accent);transform:translateY(-2px)}
.dep-arrow{color:var(--text2);font-size:20px;margin:0 8px}
.detail-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:100;backdrop-filter:blur(4px)}
.detail-overlay.open{display:flex;align-items:center;justify-content:center;animation:fadeIn .3s}
.detail-panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);width:90%;max-width:900px;max-height:85vh;overflow-y:auto;padding:40px;position:relative}
.detail-close{position:absolute;top:16px;right:16px;background:var(--surface2);border:none;color:var(--text);width:36px;height:36px;border-radius:50%;cursor:pointer;font-size:18px;display:flex;align-items:center;justify-content:center;transition:all .2s}
.detail-close:hover{background:var(--red)}
.phase-card{position:relative;overflow:hidden;padding-left:32px}
.phase-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:4px;border-radius:2px}
.phase-card.ph0::before{background:var(--red)}.phase-card.ph1::before{background:var(--orange)}
.phase-card.ph2::before{background:var(--yellow)}.phase-card.ph3::before{background:var(--green)}
.exec-summary{border-left:4px solid var(--accent);padding-left:28px}
.strength-item,.gap-item{padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;color:var(--text2);line-height:1.6}
.strength-item::before{content:'✅ ';}.gap-item::before{content:'⚠️ ';}
@media(max-width:768px){.container{padding:16px}.header h1{font-size:28px}.score-hero{flex-direction:column;gap:32px}.grid-2,.grid-3,.grid-4{grid-template-columns:1fr}.cat-row{flex-direction:column;gap:8px}.cat-label{width:100%}}
::-webkit-scrollbar{width:8px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}::-webkit-scrollbar-thumb:hover{background:var(--text2)}
</style>
'''

# ── JavaScript ───────────────────────────────────────────────────────────────
JS_BLOCK = r'''
Chart.register(ChartDataLabels);
const C = {green:'#00cec9',yellow:'#fdcb6e',orange:'#e17055',red:'#d63031',accent:'#6c5ce7',accent2:'#a29bfe',blue:'#0984e3',text2:'#9ca0b0',surface2:'#232733'};
function scColor(s){if(s>=3.5)return C.green;if(s>=2.5)return C.yellow;if(s>=1.5)return C.orange;return C.red}
function tierName(s){if(s>=3.5)return'Agent-Ready';if(s>=2.5)return'Partial';if(s>=1.5)return'Needs Work';return'Not Ready'}
function tierClass(s){if(s>=3.5)return'tier-green';if(s>=2.5)return'tier-yellow';if(s>=1.5)return'tier-orange';return'tier-red'}

// Navigation
function showSection(id, btn){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('sec-'+id).classList.add('active');
  if(btn) btn.classList.add('active');
}

// Score Ring
const ringCtx=document.getElementById('scoreRing').getContext('2d');
new Chart(ringCtx,{type:'doughnut',data:{datasets:[{data:[DATA.score,4-DATA.score],backgroundColor:[scColor(DATA.score),'rgba(45,49,64,.5)'],borderWidth:0,cutout:'78%'}]},options:{responsive:false,plugins:{legend:{display:false},tooltip:{enabled:false},datalabels:{display:false}},animation:{animateRotate:true,duration:1500}}});
// Animate score number
let cur=0;const tgt=DATA.score;const heroEl=document.getElementById('heroScore');
const anim=setInterval(()=>{cur+=0.05;if(cur>=tgt){cur=tgt;clearInterval(anim)}heroEl.textContent=cur.toFixed(1)},30);

// Executive Summary
document.getElementById('execSummary').textContent=DATA.summary;

// Category Bars
const catBarsEl=document.getElementById('catBars');
DATA.categories.forEach(c=>{
  const pct=Math.min(100,(c.score/4)*100);
  catBarsEl.innerHTML+=`<div class="cat-row"><div class="cat-label">${c.name}</div><div class="cat-bar-wrap"><div class="cat-bar-track"><div class="cat-bar-fill" style="width:${pct}%;background:${scColor(c.score)}"></div></div><div class="cat-score" style="color:${scColor(c.score)}">${c.score}/4.0</div></div></div>`;
});

// Strengths & Gaps lists
const strEl=document.getElementById('strengthsList');
DATA.strengths.forEach(s=>{strEl.innerHTML+=`<li class="strength-item">${s}</li>`});
const gapEl=document.getElementById('gapsList');
DATA.commonGaps.forEach(g=>{gapEl.innerHTML+=`<li class="gap-item">${g}</li>`});
'''

JS_BLOCK += r'''
// Service Cards
const svcEl=document.getElementById('serviceCards');
DATA.services.forEach(s=>{
  const cats=Object.entries(s.categories).map(([k,v])=>`<div class="svc-bar-row"><div class="svc-bar-label">${k}</div><div class="svc-bar-track"><div class="svc-bar-fill" style="width:${(v/4)*100}%;background:${scColor(v)}"></div></div><span style="font-size:11px;color:${scColor(v)};width:40px;text-align:right">${v}</span></div>`).join('');
  svcEl.innerHTML+=`<div class="card svc-card ${tierClass(s.score)}" onclick="openDetail('${s.name}')"><div class="svc-name">${s.name}</div><div class="svc-score" style="color:${scColor(s.score)}">${s.score}<span style="font-size:16px;color:var(--text2)"> / 4.0</span></div><div style="font-size:12px;color:var(--text2);margin-bottom:12px">${tierName(s.score)}</div>${cats}<div class="svc-priority ${s.priority.toLowerCase()}">${s.priority}</div></div>`;
});

// Radar Chart
const catLabels=DATA.categories.map(c=>c.name.replace('&','&'));
const svcColors=[C.accent,C.green,C.orange,C.red,C.blue,C.yellow];
const radarDS=DATA.services.map((s,i)=>({label:s.name,data:catLabels.map((_,ci)=>{const k=Object.keys(s.categories)[ci];return s.categories[k]||0}),borderColor:svcColors[i%svcColors.length],backgroundColor:svcColors[i%svcColors.length]+'33',pointRadius:4,pointHoverRadius:6,borderWidth:2}));
new Chart(document.getElementById('radarChart'),{type:'radar',data:{labels:catLabels,datasets:radarDS},options:{scales:{r:{min:0,max:4,ticks:{stepSize:1,color:C.text2,backdropColor:'transparent'},grid:{color:'rgba(45,49,64,.8)'},pointLabels:{color:'#e4e6f0',font:{size:12}}}},plugins:{legend:{labels:{color:'#e4e6f0',font:{size:12}}},datalabels:{display:false}}}});

// Heatmap
const heatCtx=document.getElementById('heatmapChart');
const heatDS=DATA.services.map((s,si)=>({label:s.name,data:Object.values(s.categories),backgroundColor:Object.values(s.categories).map(v=>scColor(v)+'cc'),borderColor:'transparent',borderWidth:2,borderRadius:6,barPercentage:.85,categoryPercentage:.85}));
new Chart(heatCtx,{type:'bar',data:{labels:Object.keys(DATA.services[0]?.categories||{}),datasets:heatDS},options:{indexAxis:'y',scales:{x:{grid:{color:'rgba(45,49,64,.5)'},ticks:{color:C.text2},max:4},y:{grid:{display:false},ticks:{color:'#e4e6f0'}}},plugins:{legend:{labels:{color:'#e4e6f0'}},datalabels:{color:'#fff',font:{size:10,weight:'bold'},formatter:function(val){return typeof val==='number'?val.toFixed(1):val}}}}});
'''

JS_BLOCK += r'''
// Gap Tables
function fillGapTable(id,gaps){
  const el=document.getElementById(id);
  gaps.forEach(g=>{
    el.innerHTML+=`<tr><td><span style="color:var(--accent2);font-weight:600">${g.id}</span></td><td>${g.title}</td><td>${g.score}</td><td>${g.affected} of ${DATA.services.length}</td><td style="color:var(--text2);font-size:12px">${g.impact||g.rec||'—'}</td></tr>`;
  });
}
fillGapTable('blockingTable',DATA.blocking);
fillGapTable('generalTable',DATA.general);

// Dependencies
const depViz=document.getElementById('depViz');
if(DATA.deps.length>0){
  // Build SVG dependency graph
  const nodes=[...new Set(DATA.deps.flatMap(d=>[d.source,d.target]))];
  // Also add isolated services
  DATA.services.forEach(s=>{if(!nodes.includes(s.name))nodes.push(s.name)});
  const w=860,h=Math.max(300,nodes.length*90);
  const cols=Math.min(nodes.length,3);
  let svg=`<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">`;
  svg+=`<defs><marker id="arrS" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="${C.orange}"/></marker>`;
  svg+=`<marker id="arrA" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="${C.green}"/></marker></defs>`;
  // Position nodes
  const pos={};
  nodes.forEach((n,i)=>{
    const col=i%cols,row=Math.floor(i/cols);
    pos[n]={x:140+col*280,y:60+row*120};
  });
  // Draw edges
  DATA.deps.forEach(d=>{
    const s=pos[d.source],t=pos[d.target];
    if(s&&t){
      const mk=d.type==='sync'?'arrS':'arrA';
      const cl=d.type==='sync'?C.orange:C.green;
      const dash=d.type==='sync'?'stroke-dasharray="8,4"':'';
      svg+=`<line x1="${s.x}" y1="${s.y+40}" x2="${t.x}" y2="${t.y}" stroke="${cl}" stroke-width="2" ${dash} marker-end="url(#${mk})" opacity=".7"/>`;
      svg+=`<text x="${(s.x+t.x)/2+10}" y="${(s.y+40+t.y)/2}" fill="${cl}" font-size="11" font-weight="600">${d.type.toUpperCase()}</text>`;
    }
  });
  // Draw nodes
  nodes.forEach(n=>{
    const p=pos[n];
    const svc=DATA.services.find(s=>s.name===n);
    const sc=svc?svc.score:0;
    svg+=`<rect x="${p.x-110}" y="${p.y-25}" width="220" height="65" rx="12" fill="#1a1d27" stroke="${scColor(sc)}" stroke-width="2"/>`;
    svg+=`<text x="${p.x}" y="${p.y+2}" fill="#e4e6f0" font-size="13" font-weight="700" text-anchor="middle">${n}</text>`;
    svg+=`<text x="${p.x}" y="${p.y+20}" fill="${scColor(sc)}" font-size="11" font-weight="600" text-anchor="middle">${sc.toFixed(1)}/4.0 · ${svc?svc.priority:'—'}</text>`;
  });
  svg+=`</svg>`;
  depViz.innerHTML=svg;
} else {
  depViz.innerHTML='<p style="color:var(--text2);text-align:center">No inter-service dependencies detected</p>';
}

// Dep table
const depTbl=document.getElementById('depTable');
DATA.deps.forEach(d=>{
  const risk=d.type==='sync'?'<span class="gap-dot" style="background:var(--red)"></span>High':'<span class="gap-dot" style="background:var(--yellow)"></span>Moderate';
  depTbl.innerHTML+=`<tr><td>${d.source} → ${d.target}</td><td style="color:${d.type==='sync'?C.orange:C.green}">${d.type.toUpperCase()}</td><td>${risk}</td></tr>`;
});
if(DATA.deps.length===0) depTbl.innerHTML='<tr><td colspan="3" style="text-align:center;color:var(--text2)">No dependencies</td></tr>';
'''

JS_BLOCK += r'''
// Quick Wins
const qwEl=document.getElementById('quickWinsList');
const qwIcons=['🤖','🔗','💬','📚','🚀','🔄','📊','⚙️'];
if(DATA.quickWins.length>0){
  DATA.quickWins.forEach((q,i)=>{
    qwEl.innerHTML+=`<div style="background:var(--surface2);border-radius:12px;padding:16px;border-left:3px solid ${[C.accent,C.green,C.blue,C.yellow,C.orange][i%5]}"><div style="font-size:14px;font-weight:700;margin-bottom:4px">${qwIcons[i%qwIcons.length]} ${q.title}</div><div style="font-size:11px;color:var(--accent2);margin-bottom:8px">${q.repos}</div><div style="font-size:12px;color:var(--text2);line-height:1.6">${q.description}</div></div>`;
  });
} else {
  document.getElementById('quickWinsCard').style.display='none';
}

// Pathways
const pwIcons={'Move to Cloud Native':'☁️','Move to Containers':'📦','Move to Open Source':'🔓','Move to Managed Databases':'🗄️','Move to Managed Analytics':'📊','Move to Modern DevOps':'🔧','Move to AI':'🤖'};
if(DATA.pathways.length>0){
  // Pathway bar chart
  new Chart(document.getElementById('pathwayChart'),{
    type:'bar',
    data:{
      labels:DATA.pathways.map(p=>p.name.replace('Move to ','')),
      datasets:[{
        label:'Services Triggered',
        data:DATA.pathways.map(p=>p.triggered),
        backgroundColor:DATA.pathways.map(p=>{
          if(p.priority==='High')return C.accent+'cc';
          if(p.priority==='Medium')return C.yellow+'cc';
          return C.text2+'66';
        }),
        borderColor:DATA.pathways.map(p=>{
          if(p.priority==='High')return C.accent;
          if(p.priority==='Medium')return C.yellow;
          return C.text2;
        }),
        borderWidth:1,borderRadius:8
      }]
    },
    options:{
      scales:{
        y:{beginAtZero:true,max:DATA.pathways[0]?.total||4,grid:{color:'rgba(45,49,64,.5)'},ticks:{color:C.text2,stepSize:1},title:{display:true,text:'Services',color:C.text2}},
        x:{grid:{display:false},ticks:{color:'#e4e6f0',font:{size:11}}}
      },
      plugins:{legend:{display:false},datalabels:{color:'#fff',font:{weight:'bold'},formatter:v=>v+'/'+DATA.pathways[0]?.total}}
    }
  });

  // Pathway cards
  const pwCardsEl=document.getElementById('pathwayCards');
  const prioColors={'High':C.red,'Medium':C.yellow,'Low':C.text2};
  const effColors={'High':C.red,'Medium':C.orange,'Low':C.green,'N/A':C.text2};
  DATA.pathways.forEach(p=>{
    const icon=pwIcons[p.name]||'🔹';
    const pctVal=Math.round((p.triggered/p.total)*100);
    pwCardsEl.innerHTML+=`<div class="card" style="position:relative;overflow:hidden"><div style="position:absolute;top:0;left:0;right:0;height:3px;background:${prioColors[p.priority]||C.accent}"></div><div style="font-size:24px;margin-bottom:8px">${icon}</div><div style="font-size:14px;font-weight:700;margin-bottom:4px">${p.name}</div><div style="font-size:28px;font-weight:800;color:${pctVal===100?C.green:pctVal>=50?C.yellow:C.text2};margin-bottom:4px">${pctVal}%</div><div style="font-size:12px;color:var(--text2);margin-bottom:8px">${p.triggered} of ${p.total} services</div><div style="display:flex;gap:8px;flex-wrap:wrap"><span style="padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;background:${prioColors[p.priority]||C.accent}22;color:${prioColors[p.priority]||C.accent}">${p.priority} Priority</span><span style="padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;background:${effColors[p.effort]||C.text2}22;color:${effColors[p.effort]||C.text2}">${p.effort} Effort</span></div></div>`;
  });

  // Pathway × Service matrix table
  const matEl=document.getElementById('pathwayMatrix');
  const svcNames=DATA.services.map(s=>s.name);
  let matHtml='<table class="gap-table"><thead><tr><th>Pathway</th>';
  svcNames.forEach(s=>{matHtml+=`<th style="text-align:center">${s}</th>`});
  matHtml+='<th style="text-align:center">Coverage</th></tr></thead><tbody>';
  DATA.pathways.forEach(p=>{
    matHtml+=`<tr><td style="font-weight:600">${pwIcons[p.name]||''} ${p.name}</td>`;
    let cnt=0;
    svcNames.forEach(s=>{
      const triggered=p.perService[s]===true;
      if(triggered)cnt++;
      matHtml+=`<td style="text-align:center;font-size:16px">${triggered?'✅':'—'}</td>`;
    });
    const covPct=Math.round((cnt/svcNames.length)*100);
    matHtml+=`<td style="text-align:center;font-weight:700;color:${covPct===100?C.green:covPct>=50?C.yellow:C.text2}">${covPct}%</td></tr>`;
  });
  matHtml+='</tbody></table>';
  matEl.innerHTML=matHtml;
}

// Roadmap Gantt Chart
if(DATA.phases.length>0){
  const phColors=[C.red,C.orange,C.yellow,C.green,C.blue,C.accent];
  // Parse timeframes like "Mo 0-1", "Mo 1-2", etc.
  const phData=DATA.phases.map((p,i)=>{
    const m=p.timeframe.match(/(\d+)[–\-](\d+\+?)/);
    const start=m?parseInt(m[1]):i*2;
    const end=m?parseInt(m[2]):start+2;
    return{label:p.name,start,end,color:phColors[i%phColors.length]};
  });
  const maxMo=Math.max(...phData.map(p=>p.end))+1;
  new Chart(document.getElementById('ganttChart'),{
    type:'bar',
    data:{
      labels:phData.map(p=>p.label),
      datasets:[
        {label:'Start',data:phData.map(p=>p.start),backgroundColor:'transparent',borderWidth:0},
        {label:'Duration',data:phData.map(p=>p.end-p.start),backgroundColor:phData.map(p=>p.color+'cc'),borderColor:phData.map(p=>p.color),borderWidth:1,borderRadius:6}
      ]
    },
    options:{
      indexAxis:'y',
      scales:{
        x:{stacked:true,min:0,max:maxMo,title:{display:true,text:'Months',color:C.text2},grid:{color:'rgba(45,49,64,.5)'},ticks:{color:C.text2,stepSize:1}},
        y:{stacked:true,grid:{display:false},ticks:{color:'#e4e6f0',font:{size:11}}}
      },
      plugins:{legend:{display:false},datalabels:{display:false},tooltip:{callbacks:{label:ctx=>ctx.datasetIndex===1?`${ctx.raw} months`:''}}}
    }
  });
}

// Phase Cards
const phEl=document.getElementById('phaseCards');
DATA.phases.forEach((p,i)=>{
  phEl.innerHTML+=`<div class="card phase-card ph${i}"><div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:${[C.red,C.orange,C.yellow,C.green,C.blue][i%5]};margin-bottom:8px">${p.name}</div><div style="font-size:11px;color:var(--text2);margin-bottom:12px">${p.timeframe}</div><p style="font-size:13px;line-height:1.7;color:var(--text2)">${p.objective}</p></div>`;
});

// Detail Panel
function openDetail(name){
  const svc=DATA.services.find(s=>s.name===name);
  if(!svc)return;
  const panel=document.getElementById('detailPanel');
  const cats=Object.entries(svc.categories).map(([k,v])=>`<div class="cat-row"><div class="cat-label">${k}</div><div class="cat-bar-wrap"><div class="cat-bar-track"><div class="cat-bar-fill" style="width:${(v/4)*100}%;background:${scColor(v)}"></div></div><div class="cat-score" style="color:${scColor(v)}">${v}/4.0</div></div></div>`).join('');
  // Find related deps
  const relDeps=DATA.deps.filter(d=>d.source===name||d.target===name);
  const depHtml=relDeps.length?relDeps.map(d=>`<div style="padding:6px 0;font-size:13px;color:var(--text2)">${d.source} → ${d.target} <span style="color:${d.type==='sync'?C.orange:C.green}">(${d.type})</span></div>`).join(''):'<div style="color:var(--text2);font-size:13px">No dependencies (isolated)</div>';
  // Find related gaps
  const relGaps=DATA.blocking.concat(DATA.general).filter(g=>g.affected>=DATA.services.length-1);
  const gapHtml=relGaps.slice(0,5).map(g=>`<div style="padding:6px 0;font-size:13px;border-bottom:1px solid var(--border)"><span style="color:var(--accent2);font-weight:600">${g.id}</span> ${g.title} — <span style="color:var(--red)">${g.score}</span></div>`).join('');

  panel.innerHTML=`<button class="detail-close" onclick="closeDetail()">✕</button>
    <h2 style="font-size:24px;font-weight:800;margin-bottom:4px">${svc.name}</h2>
    <div style="color:var(--text2);font-size:13px;margin-bottom:24px">${tierName(svc.score)} · ${svc.priority}</div>
    <div style="font-size:56px;font-weight:900;text-align:center;color:${scColor(svc.score)};margin:16px 0">${svc.score}<span style="font-size:20px;color:var(--text2)"> / 4.0</span></div>
    <div style="margin:24px 0"><div class="card-title">Category Breakdown</div>${cats}</div>
    <div class="grid grid-2">
      <div><div class="card-title">Dependencies</div>${depHtml}</div>
      <div><div class="card-title">Top Gaps Affecting This Service</div>${gapHtml||'<div style="color:var(--text2);font-size:13px">No cross-cutting gaps</div>'}</div>
    </div>`;
  document.getElementById('detailOverlay').classList.add('open');
}
function closeDetail(){document.getElementById('detailOverlay').classList.remove('open')}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDetail()});
'''


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate an interactive HTML dashboard from a portfolio agentic readiness assessment report."
    )
    parser.add_argument("report", help="Path to the portfolio assessment markdown file")
    parser.add_argument("-o", "--output", help="Output HTML file path (default: dashboard.html in same dir as report)")
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Error: Report file not found: {report_path}")
        sys.exit(1)

    content = report_path.read_text(encoding="utf-8")
    print(f"Parsing report: {report_path.name} ({len(content)} chars)")

    data = parse_report(content)
    print(f"  Portfolio: {data.name}")
    print(f"  Score: {data.score}/4.0")
    print(f"  Services: {len(data.services)}")
    print(f"  Categories: {len(data.categories)}")
    print(f"  Blocking gaps: {len(data.blocking_gaps)}")
    print(f"  General gaps: {len(data.general_gaps)}")
    print(f"  Dependencies: {len(data.deps)}")
    print(f"  Roadmap phases: {len(data.phases)}")
    print(f"  Pathways: {len(data.pathways)}")
    print(f"  Quick wins: {len(data.quick_wins)}")

    html = generate_html(data)

    out_path = Path(args.output) if args.output else report_path.parent / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"\nDashboard generated: {out_path} ({len(html)} chars)")
    print(f"Open in browser: file://{out_path.resolve()}")


if __name__ == "__main__":
    main()
