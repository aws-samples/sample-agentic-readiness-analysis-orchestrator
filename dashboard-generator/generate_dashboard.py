#!/usr/bin/env python3
"""
Agentic Readiness Dashboard Generator

Parses portfolio OR individual agentic readiness assessment markdown reports
and generates an interactive CAST-style HTML dashboard.

Usage:
    python generate_dashboard.py <report.md> [-o output.html]
    python generate_dashboard.py <directory>   # batch mode

Example:
    python generate_dashboard.py ../example-reports/agentic-readiness-assessment/books-api-agentic-readiness-report.md
    python generate_dashboard.py ../example-reports/agentic-readiness-assessment/ecommerce-platform-test-portfolio-agentic-readiness-report.md
"""

import re, json, sys, argparse, html as html_mod
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class ServiceScore:
    name: str; score: float; priority: str = "P0"; categories: dict = field(default_factory=dict)

@dataclass
class CategoryScore:
    name: str; score: float; status: str = ""

@dataclass
class Gap:
    id: str; title: str; score: str; affected: int; impact: str = ""; recommendation: str = ""; is_blocking: bool = False

@dataclass
class Phase:
    name: str; timeframe: str; objective: str; effort: str = "High"

@dataclass
class Dep:
    source: str; target: str; dtype: str

@dataclass
class Pathway:
    name: str; services_triggered: int; total_services: int; priority: str = "High"
    effort: str = "High"; per_service: dict = field(default_factory=dict)
    status: str = ""; goal_alignment: str = ""

@dataclass
class QuickWin:
    title: str; repos: str; description: str

@dataclass
class QuestionScore:
    qid: str; title: str; score: int; max_score: int = 4
    finding: str = ""; gap: str = ""; recommendation: str = ""; category: str = ""

@dataclass
class Portfolio:
    name: str = ""; goal: str = ""; goal_context: str = ""; date: str = ""
    total_services: int = 0; score: float = 0.0; is_individual: bool = False
    services: List[ServiceScore] = field(default_factory=list)
    categories: List[CategoryScore] = field(default_factory=list)
    blocking_gaps: List[Gap] = field(default_factory=list)
    general_gaps: List[Gap] = field(default_factory=list)
    phases: List[Phase] = field(default_factory=list)
    deps: List[Dep] = field(default_factory=list)
    pathways: List[Pathway] = field(default_factory=list)
    quick_wins: List[QuickWin] = field(default_factory=list)
    questions: List[QuestionScore] = field(default_factory=list)
    summary: str = ""; strengths: list = field(default_factory=list)
    common_gaps: list = field(default_factory=list)


# ── Shared Helpers ───────────────────────────────────────────────────────────

def get_section(content: str, heading: str) -> Optional[str]:
    pat3 = rf'(?:^|\n)###\s*{re.escape(heading)}\s*\n(.*?)(?=\n###\s|\n##[^#]|\n---|\Z)'
    m3 = re.search(pat3, content, re.DOTALL)
    if m3: return m3.group(1)
    pat2 = rf'(?:^|\n)##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##\s|\n---|\Z)'
    m2 = re.search(pat2, content, re.DOTALL)
    if m2: return m2.group(1)
    pat = rf'{re.escape(heading)}\s*\n(.*?)(?=\n##|\n---|\Z)'
    m = re.search(pat, content, re.DOTALL)
    return m.group(1) if m else None

def detect_report_type(content: str) -> str:
    if re.search(r'\*\*Services Assessed\*\*:', content[:600]):
        return "portfolio"
    if re.search(r'\*\*Target\*\*:', content[:600]):
        return "individual"
    if '## Executive Dashboard' in content[:2000]:
        return "portfolio"
    return "individual"

def _esc(s):
    return s.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace('\u2014', '-').replace('\u2013', '-')


# ── Individual Report Parser ─────────────────────────────────────────────────

def parse_individual_report(content: str) -> Portfolio:
    d = Portfolio(is_individual=True)

    for key, attr in [("Target", "name"), ("Assessment Goal", "goal"),
                      ("Goal Context", "goal_context"), ("Date", "date")]:
        m = re.search(rf'\*\*{key}\*\*:\s*(.+)', content)
        if m: setattr(d, attr, m.group(1).strip())

    m = re.search(r'Overall Score:\s*([\d.]+)\s*/\s*4\.0', content)
    if m: d.score = float(m.group(1))

    # Executive summary
    sec = get_section(content, "Executive Summary")
    if sec:
        paras = [p.strip() for p in sec.split('\n\n')
                 if p.strip() and not p.strip().startswith(('#', '|', '---', '*'))]
        if paras: d.summary = paras[0]

    # Categories from score table
    cats = re.findall(
        r'\|\s*(Infrastructure[^|]*|Application[^|]*|Data[^|]*|Identity[^|]*|Operations[^|]*)\s*\|\s*([\d.]+)\s*/\s*4\.0\s*\|\s*([^\|]+)\|',
        content)
    cat_map = {"Infrastructure": "INF", "Application": "APP", "Data": "DATA",
               "Identity": "SEC", "Operations": "OPS"}
    for name, score, status in cats:
        d.categories.append(CategoryScore(name.strip(), float(score), status.strip()))

    # Top Priorities (blocking gaps)
    tp_sec = get_section(content, "Top Priorities (Critical Gaps)")
    if tp_sec:
        blocks = re.split(r'\n###\s*\d+\.', tp_sec)
        for block in blocks:
            m = re.match(r'\s*(\w+-\w+):\s*(.+?)\s*[\u2014\u2013\-]+\s*Score\s*(\d+)/(\d+)', block)
            if m:
                g = Gap(id=m.group(1), title=m.group(2).strip(), score=f"{m.group(3)}/{m.group(4)}",
                        affected=1, is_blocking=True)
                fm = re.search(r'\*\*First step\*\*:\s*([^\n]+)', block)
                if fm: g.recommendation = fm.group(1).strip()
                d.blocking_gaps.append(g)

    # Detailed findings - per-question scores
    cat_shorts = {"Infrastructure & Platform": "INF", "Application Architecture": "APP",
                  "Data Foundations": "DATA", "Identity, Security & Governance": "SEC",
                  "Operations & Observability": "OPS"}
    for cat_heading, prefix in cat_shorts.items():
        sec2 = get_section(content, cat_heading)
        if not sec2: continue
        q_blocks = re.split(r'\n####\s+', sec2)
        for qb in q_blocks:
            qm = re.match(r'(\w+-Q\d+):\s*(.+)', qb)
            if not qm: continue
            qid, title = qm.group(1), qm.group(2).strip()
            sm = re.search(r'\*\*Score\*\*:\s*(\d+)/(\d+)', qb)
            score_val = int(sm.group(1)) if sm else 0
            max_val = int(sm.group(2)) if sm else 4
            finding = ""; gap_text = ""; rec = ""
            fm2 = re.search(r'\*\*Finding\*\*:\s*(.+?)(?=\n-\s*\*\*|\Z)', qb, re.DOTALL)
            if fm2: finding = fm2.group(1).strip()
            gm = re.search(r'\*\*Gap\*\*:\s*(.+?)(?=\n-\s*\*\*|\Z)', qb, re.DOTALL)
            if gm: gap_text = gm.group(1).strip()
            rm = re.search(r'\*\*Recommendation\*\*:\s*(.+?)(?=\n####|\n###|\Z)', qb, re.DOTALL)
            if rm: rec = rm.group(1).strip()
            d.questions.append(QuestionScore(qid=qid, title=title, score=score_val,
                                             max_score=max_val, finding=finding, gap=gap_text,
                                             recommendation=rec, category=prefix))

    # Pathways
    pw_sec = get_section(content, "Recommended Modernization Pathways") or get_section(content, "Pathway Summary")
    if pw_sec:
        pw_rows = re.findall(
            r'\|\s*(Move to [^|]+?)\s*\|\s*(Triggered|Not Triggered)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|[^|]*\|\s*([^|]*?)\s*\|',
            pw_sec)
        for pname, status, alignment, priority, effort in pw_rows:
            pw = Pathway(name=pname.strip(), services_triggered=1 if status == "Triggered" else 0,
                         total_services=1, priority=priority.strip() or "—",
                         effort=effort.strip() or "—", status=status.strip(),
                         goal_alignment=alignment.strip())
            d.pathways.append(pw)

    # Quick wins
    qw_sec = get_section(content, "Quick Agent Wins")
    if qw_sec:
        qw_blocks = re.split(r'\n\d+\.\s+\*\*', qw_sec)
        for block in qw_blocks:
            tm = re.match(r'([^*]+)\*\*\s*[\u2014\u2013\-]+\s*(.+?)(?=\n\d+\.\s+\*\*|\Z)', block, re.DOTALL)
            if tm:
                title = tm.group(1).strip()
                desc = tm.group(2).strip()[:300]
                lev = re.search(r'\*\*Leverages\*\*:\s*([^\n]+)', block)
                repos = lev.group(1).strip() if lev else ""
                d.quick_wins.append(QuickWin(title=title, repos=repos, description=desc))

    # Roadmap phases
    rmap = get_section(content, "Readiness Roadmap")
    if rmap:
        for m in re.finditer(r'###\s*Phase\s*(\d+)\s*[\u2014\u2013\-]+\s*([^(]+)\(([^)]+)\)', rmap):
            obj_m = re.search(rf'Phase\s*{m.group(1)}.*?\n\n(.+?)(?=\n\n\d+\.|\n###|\Z)', rmap[m.start():], re.DOTALL)
            obj = obj_m.group(1).strip()[:200] if obj_m else ""
            d.phases.append(Phase(f"Phase {m.group(1)} — {m.group(2).strip()}", m.group(3).strip(), obj))

    return d


# ── Portfolio Report Parser ──────────────────────────────────────────────────

def parse_portfolio_report(content: str) -> Portfolio:
    d = Portfolio()

    for key, attr in [("Portfolio", "name"), ("Assessment Goal", "goal"),
                      ("Goal Context", "goal_context"), ("Assessment Date", "date")]:
        m = re.search(rf'\*\*{key}\*\*:\s*(.+)', content)
        if m: setattr(d, attr, m.group(1).strip())

    m = re.search(r'\*\*Services Assessed\*\*:\s*(\d+)', content)
    if m: d.total_services = int(m.group(1))

    m = re.search(r'Portfolio Readiness Score:\s*([\d.]+)\s*/\s*4\.0', content)
    if m: d.score = float(m.group(1))

    sec = get_section(content, "Executive Dashboard")
    if sec:
        paras = [p.strip() for p in sec.split('\n\n')
                 if p.strip() and not p.strip().startswith(('#', '|', '---', '*'))]
        if paras: d.summary = paras[0]

    cats = re.findall(
        r'\|\s*(Infrastructure[^|]*|Application[^|]*|Data[^|]*|Identity[^|]*|Operations[^|]*)\s*\|\s*([\d.]+)\s*/\s*4\.0\s*\|[^|]*\|\s*([^\|]+)\|',
        content)
    for name, score, status in cats:
        d.categories.append(CategoryScore(name.strip(), float(score), status.strip()))

    # Services from readiness distribution
    svcs = re.findall(r'[\u2014\u2013\-]\s*([\w][\w-]+)\s*\(([\d.]+)\)', content[:5000])
    svcs += re.findall(r',\s*([\w][\w-]+)\s*\(([\d.]+)\)', content[:5000])
    seen = set()
    for name, score in svcs:
        if name in seen or len(name) < 4 or name in ('services', 'service'): continue
        try:
            sc_val = float(score)
            if sc_val > 4.0 or sc_val < 0: continue
        except ValueError: continue
        if not re.search(rf'\|\s*{re.escape(name)}\s', content): continue
        seen.add(name)
        s = ServiceScore(name=name, score=sc_val)
        pm = re.search(rf'{re.escape(name)}.*?(P[012])', content)
        if pm: s.priority = pm.group(1)
        d.services.append(s)

    # Per-service category scores
    cat_shorts = {"Infrastructure": "INF", "Application": "APP",
                  "Data": "DATA", "Identity": "SEC", "Operations": "OPS"}
    for svc in d.services:
        for cat in d.categories:
            short = next((v for k, v in cat_shorts.items() if k in cat.name), cat.name[:3].upper())
            sec2 = get_section(content, cat.name)
            if sec2:
                pm2 = re.search(rf'{re.escape(svc.name)}[^)]*?\(?([\d.]+)/4\.0', sec2)
                if pm2: svc.categories[short] = float(pm2.group(1))
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
        for m in re.finditer(r'([\w-]+)\s*\u2192\s*([\w-]+).*?(sync|async|SYNC|ASYNC|REST|EventBridge)', dep_sec):
            dt = "sync" if any(x in m.group(3).lower() for x in ["sync", "rest"]) else "async"
            key = (m.group(1), m.group(2), dt)
            if key not in seen_deps:
                seen_deps.add(key)
                d.deps.append(Dep(m.group(1), m.group(2), dt))

    # Roadmap phases
    rmap = get_section(content, "Portfolio Modernization Roadmap")
    if rmap:
        for m in re.finditer(r'###\s*Phase\s*(\d+)\s*[\u2014\u2013\-]+\s*([^(]+)\(([^)]+)\)\s*\n\n\*\*Objective\*\*:\s*([^\n]+)', rmap):
            d.phases.append(Phase(f"Phase {m.group(1)} \u2014 {m.group(2).strip()}", m.group(3).strip(), m.group(4).strip()))

    # Strengths and common gaps
    ss = get_section(content, "Common Strengths")
    if ss: d.strengths = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', ss)
    gs = get_section(content, "Common Gaps")
    if gs: d.common_gaps = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', gs)

    # Modernization Pathways
    pw_sec = get_section(content, "AWS Modernization Pathways")
    if pw_sec:
        pw_rows = re.findall(
            r'\|\s*(Move to [^|]+?)\s*\|\s*(\d+)\s*services?\s*\|\s*(\d+)%[^|]*\|\s*(\w+)\s*\|\s*([^\|]*?)\s*\|',
            pw_sec)
        svc_names = [s.name for s in d.services]
        n_svc = d.total_services or len(d.services)
        for pname, triggered, pct_val, priority, effort in pw_rows:
            pw = Pathway(name=pname.strip(), services_triggered=int(triggered),
                         total_services=n_svc, priority=priority.strip(),
                         effort=effort.strip().rstrip('\u2014').strip() or "N/A")
            d.pathways.append(pw)

        # Per-service pathway assignment table
        assign_start = pw_sec.find('Per-Service Pathway Assignment')
        if assign_start >= 0 and d.pathways:
            assign_chunk = pw_sec[assign_start:assign_start + 1500]
            header_m = re.search(r'\|\s*Service\s*\|([^\n]+)', assign_chunk)
            if header_m:
                col_names = [h.strip() for h in header_m.group(1).split('|') if h.strip()]
                col_to_pw = {}
                for ci, col in enumerate(col_names):
                    col_lower = col.lower().replace('move to ', '').strip()
                    best_pw = None; best_score = 0
                    for pw in d.pathways:
                        pw_short = pw.name.lower().replace('move to ', '').strip()
                        if col_lower == pw_short: best_pw = pw; break
                        if pw_short.startswith(col_lower) and len(col_lower) > best_score:
                            best_pw = pw; best_score = len(col_lower)
                        elif col_lower.startswith(pw_short) and len(pw_short) > best_score:
                            best_pw = pw; best_score = len(pw_short)
                        else:
                            col_words = col_lower.split(); pw_words = pw_short.split()
                            if col_words and all(any(pww.startswith(cw) for pww in pw_words) for cw in col_words):
                                if len(col_lower) > best_score: best_pw = pw; best_score = len(col_lower)
                    if best_pw: col_to_pw[ci] = best_pw
                for svc in d.services:
                    row_m = re.search(rf'\|\s*{re.escape(svc.name)}\s*\|([^\n]+)', assign_chunk)
                    if row_m:
                        raw_cells = row_m.group(1).split('|')
                        for ci, pw in col_to_pw.items():
                            if ci < len(raw_cells):
                                cell = raw_cells[ci].strip()
                                pw.per_service[svc.name] = cell in ('\u2705', 'Yes', 'yes', '\u2713')

    # Quick Agent Wins
    qw_sec = get_section(content, "Portfolio Quick Agent Wins")
    if qw_sec:
        qw_blocks = re.split(r'\n\*\*(?=[A-Z])', qw_sec)
        for block in qw_blocks:
            tm = re.match(r'([^*]+)\*\*\s*\((\d+\s*repos?:[^)]+)\)', block)
            if tm:
                title = tm.group(1).strip(); repos = tm.group(2).strip()
                desc_text = block[tm.end():].strip()
                desc_lines = []
                for line in desc_text.split('\n'):
                    line = line.strip().lstrip('- ')
                    if not line or line.startswith('**'): break
                    desc_lines.append(line)
                d.quick_wins.append(QuickWin(title=title, repos=repos, description=' '.join(desc_lines)[:300]))

    return d


# ── Unified Parser Entry ─────────────────────────────────────────────────────

def parse_report(content: str) -> Portfolio:
    rtype = detect_report_type(content)
    if rtype == "portfolio":
        return parse_portfolio_report(content)
    return parse_individual_report(content)


# ── HTML Helpers ─────────────────────────────────────────────────────────────

def sc(score):
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
    if score >= 3.5: return "\u2705"
    if score >= 2.5: return "\U0001F7E1"
    if score >= 1.5: return "\U0001F7E0"
    return "\u274C"

def pct(score, mx=4.0):
    return min(100, max(0, (score / mx) * 100))

def generate_html(d: Portfolio) -> str:
    if d.is_individual:
        return generate_individual_html(d)
    return generate_portfolio_html(d)


# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = '''<style>
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
.gap-table{width:100%;border-collapse:collapse}
.gap-table th{text-align:left;padding:12px 16px;font-size:12px;font-weight:600;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid var(--border)}
.gap-table td{padding:12px 16px;font-size:13px;border-bottom:1px solid var(--border)}
.gap-table tr:hover td{background:var(--surface2)}
.gap-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.dep-graph{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:32px;margin:24px 0}
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
.strength-item::before{content:'\\2705 ';}.gap-item::before{content:'\\26A0\\FE0F ';}
.q-card{position:relative;overflow:hidden;cursor:pointer}
.q-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:var(--radius) var(--radius) 0 0}
.q-card.q-red::before{background:var(--red)}.q-card.q-orange::before{background:var(--orange)}
.q-card.q-yellow::before{background:var(--yellow)}.q-card.q-green::before{background:var(--green)}
@media(max-width:768px){.container{padding:16px}.header h1{font-size:28px}.score-hero{flex-direction:column;gap:32px}.grid-2,.grid-3,.grid-4{grid-template-columns:1fr}.cat-row{flex-direction:column;gap:8px}.cat-label{width:100%}}
::-webkit-scrollbar{width:8px}::-webkit-scrollbar-track{background:var(--bg)}::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}::-webkit-scrollbar-thumb:hover{background:var(--text2)}
</style>'''


# ── Shared JS ────────────────────────────────────────────────────────────────

JS_SHARED = r'''
Chart.register(ChartDataLabels);
const C={green:'#00cec9',yellow:'#fdcb6e',orange:'#e17055',red:'#d63031',accent:'#6c5ce7',accent2:'#a29bfe',blue:'#0984e3',text2:'#9ca0b0',surface2:'#232733'};
function scColor(s){if(s>=3.5)return C.green;if(s>=2.5)return C.yellow;if(s>=1.5)return C.orange;return C.red}
function tierName(s){if(s>=3.5)return'Agent-Ready';if(s>=2.5)return'Partial';if(s>=1.5)return'Needs Work';return'Not Ready'}
function tierClass(s){if(s>=3.5)return'tier-green';if(s>=2.5)return'tier-yellow';if(s>=1.5)return'tier-orange';return'tier-red'}
function showSection(id,btn){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('sec-'+id).classList.add('active');
  if(btn)btn.classList.add('active');
}
function closeDetail(){document.getElementById('detailOverlay').classList.remove('open')}
function openDetail(html){const p=document.getElementById('detailPanel');p.innerHTML='<button class="detail-close" onclick="closeDetail()">&times;</button>'+html;document.getElementById('detailOverlay').classList.add('open')}
// Score ring
function drawScoreRing(score,mx){
  const ctx=document.getElementById('scoreRing').getContext('2d');
  new Chart(ctx,{type:'doughnut',data:{datasets:[{data:[score,mx-score],backgroundColor:[scColor(score),'rgba(45,49,64,.5)'],borderWidth:0,borderRadius:6}]},options:{cutout:'78%',responsive:false,plugins:{legend:{display:false},tooltip:{enabled:false},datalabels:{display:false}},animation:{animateRotate:true,duration:1500}}});
  let cur=0;const el=document.getElementById('heroScore');const step=()=>{cur+=.03;if(cur>score)cur=score;el.textContent=cur.toFixed(2);if(cur<score)requestAnimationFrame(step)};step();
}
// Category bars
function drawCatBars(cats){
  const el=document.getElementById('catBars');if(!el)return;
  el.innerHTML=cats.map(c=>`<div class="cat-row"><div class="cat-label">${c.name}</div><div class="cat-bar-wrap"><div class="cat-bar-track"><div class="cat-bar-fill" style="width:${c.score/4*100}%;background:${scColor(c.score)}"></div></div><div class="cat-score" style="color:${scColor(c.score)}">${c.score.toFixed(1)}/4.0</div></div></div>`).join('');
}
// Gap table
function fillGapTable(id,gaps){
  const el=document.getElementById(id);if(!el)return;
  el.innerHTML=gaps.map(g=>`<tr><td><span class="gap-dot" style="background:${C.red}"></span>${g.id}</td><td>${g.title}</td><td>${g.score}</td><td>${g.affected!==undefined?g.affected+' svc':'—'}</td><td style="max-width:300px">${g.impact||g.rec||'—'}</td></tr>`).join('');
}
// Phase cards
function drawPhaseCards(phases){
  const el=document.getElementById('phaseCards');if(!el)return;
  el.innerHTML=phases.map((p,i)=>`<div class="card phase-card ph${i}"><div class="card-title">${p.name}</div><div style="font-size:13px;color:${C.accent2};margin-bottom:8px">${p.timeframe}</div><p style="font-size:13px;color:${C.text2};line-height:1.6">${p.objective}</p></div>`).join('');
}
// Gantt chart
function drawGantt(phases){
  const ctx=document.getElementById('ganttChart');if(!ctx)return;
  function parseTime(tf){
    let m=tf.match(/Days?\s*(\d+)[\s\u2013-]+(\d+)/i);if(m)return[parseInt(m.group?m[1]:m[1]),parseInt(m[2])];
    m=tf.match(/Mo(?:nths?)?\s*(\d+)[\s\u2013-]+(\d+)/i);if(m)return[parseInt(m[1])*30,parseInt(m[2])*30];
    m=tf.match(/Mo(?:nths?)?\s*(\d+)[\s\u2013-]+(\d+)\+?/i);if(m)return[parseInt(m[1])*30,parseInt(m[2])*30];
    return[0,30];
  }
  const colors=[C.red,C.orange,C.yellow,C.green,C.blue,C.accent];
  const datasets=phases.map((p,i)=>{const[s,e]=parseTime(p.timeframe);return{label:p.name,data:[{x:[s,e],y:i}],backgroundColor:colors[i%colors.length]+'99',borderColor:colors[i%colors.length],borderWidth:2,borderRadius:6,borderSkipped:false,barPercentage:.6}});
  new Chart(ctx,{type:'bar',data:{labels:phases.map(p=>p.name),datasets},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,scales:{x:{type:'linear',title:{display:true,text:'Days',color:C.text2},grid:{color:'rgba(45,49,64,.5)'},ticks:{color:C.text2}},y:{grid:{display:false},ticks:{color:C.text2,font:{size:11}}}},plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx2=>{const v=ctx2.raw.x;return ctx2.dataset.label+': Day '+v[0]+' → '+v[1]}}},datalabels:{display:false}}}});
}
// Quick wins
function drawQuickWins(qw){
  const el=document.getElementById('quickWinsList');if(!el||!qw.length){const c=document.getElementById('quickWinsCard');if(c)c.style.display='none';return}
  el.innerHTML=qw.map(q=>`<div class="card" style="padding:16px"><div style="font-size:14px;font-weight:600;margin-bottom:6px">\u26A1 ${q.title}</div><div style="font-size:12px;color:${C.accent2};margin-bottom:6px">${q.repos}</div><div style="font-size:12px;color:${C.text2};line-height:1.5">${q.description}</div></div>`).join('');
}
'''


# ── Individual JS ────────────────────────────────────────────────────────────

JS_INDIVIDUAL = r'''
// Init individual dashboard
drawScoreRing(DATA.score,4);
document.getElementById('execSummary').textContent=DATA.summary;
drawCatBars(DATA.categories);
fillGapTable('blockingTable',DATA.blocking);
drawPhaseCards(DATA.phases);
drawGantt(DATA.phases);
drawQuickWins(DATA.quickWins);

// Radar chart
(function(){
  const ctx=document.getElementById('radarChart');if(!ctx)return;
  new Chart(ctx,{type:'radar',data:{labels:DATA.categories.map(c=>c.name),datasets:[{label:'Score',data:DATA.categories.map(c=>c.score),backgroundColor:'rgba(108,92,231,.2)',borderColor:C.accent,borderWidth:2,pointBackgroundColor:DATA.categories.map(c=>scColor(c.score)),pointRadius:6}]},options:{responsive:true,maintainAspectRatio:false,scales:{r:{min:0,max:4,ticks:{stepSize:1,color:C.text2,backdropColor:'transparent'},grid:{color:'rgba(45,49,64,.5)'},pointLabels:{color:C.text2,font:{size:12}}}},plugins:{legend:{display:false},datalabels:{display:false}}}});
})();

// Question cards
let allCards='';
DATA.questions.forEach(q=>{
  const pct=q.score/q.max*100;
  const cls=q.score>=3?'q-green':q.score>=2?'q-yellow':q.score>=1?'q-orange':'q-red';
  allCards+=`<div class="card q-card ${cls}" data-cat="${q.qid.split('-')[0]}" onclick="openQuestionDetail('${q.qid}')">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <span style="font-size:12px;font-weight:700;color:${C.accent2}">${q.qid}</span>
      <span style="font-size:20px;font-weight:800;color:${scColor(q.score/q.max*4)}">${q.score}/${q.max}</span>
    </div>
    <div style="font-size:14px;font-weight:600;margin-bottom:8px">${q.title}</div>
    <div style="height:4px;background:${C.surface2};border-radius:2px;overflow:hidden"><div style="height:100%;width:${pct}%;background:${scColor(q.score/q.max*4)};border-radius:2px"></div></div>
  </div>`;
});
document.getElementById('questionCards').innerHTML=allCards;

function filterQuestions(prefix,btn){
  document.querySelectorAll('#sec-findings .nav-btn').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  document.querySelectorAll('.q-card').forEach(c=>{
    c.style.display=(prefix==='all'||c.dataset.cat===prefix)?'':'none';
  });
}

function openQuestionDetail(qid){
  const q=DATA.questions.find(x=>x.qid===qid);if(!q)return;
  openDetail(`<h2 style="font-size:24px;font-weight:800;margin-bottom:8px">${q.qid}: ${q.title}</h2>
    <div style="font-size:32px;font-weight:800;color:${scColor(q.score/q.max*4)};margin-bottom:16px">${q.score}/${q.max}</div>
    ${q.finding?'<div style="margin-bottom:16px"><div style="font-size:12px;font-weight:600;color:'+C.accent2+';margin-bottom:4px">FINDING</div><p style="font-size:13px;color:'+C.text2+';line-height:1.7">'+q.finding+'</p></div>':''}
    ${q.gap?'<div style="margin-bottom:16px"><div style="font-size:12px;font-weight:600;color:'+C.red+';margin-bottom:4px">GAP</div><p style="font-size:13px;color:'+C.text2+';line-height:1.7">'+q.gap+'</p></div>':''}
    ${q.rec?'<div><div style="font-size:12px;font-weight:600;color:'+C.green+';margin-bottom:4px">RECOMMENDATION</div><p style="font-size:13px;color:'+C.text2+';line-height:1.7">'+q.rec+'</p></div>':''}`);
}

// Heatmap
(function(){
  const ctx=document.getElementById('heatmapChart');if(!ctx)return;
  const catPrefixes=['INF','APP','DATA','SEC','OPS'];
  const grouped={};catPrefixes.forEach(p=>grouped[p]=[]);
  DATA.questions.forEach(q=>{const p=q.qid.split('-')[0];if(grouped[p])grouped[p].push(q)});
  const maxQ=Math.max(...Object.values(grouped).map(a=>a.length),1);
  const datasets=catPrefixes.map((p,yi)=>grouped[p].map((q,xi)=>({x:xi,y:yi,v:q.score,qid:q.qid}))).flat();
  new Chart(ctx,{type:'scatter',data:{datasets:[{data:datasets,pointRadius:ctx2=>{const d=ctx2.raw;return d?14:0},pointBackgroundColor:ctx2=>{const d=ctx2.raw;return d?scColor(d.v/4*4)+'cc':'transparent'},pointBorderColor:'transparent'}]},options:{responsive:true,maintainAspectRatio:false,scales:{x:{type:'linear',min:-.5,max:maxQ-.5,ticks:{display:false},grid:{display:false}},y:{type:'linear',min:-.5,max:4.5,ticks:{callback:function(v){return catPrefixes[v]||''},color:C.text2},grid:{color:'rgba(45,49,64,.3)'}}},plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx2=>{const d=ctx2.raw;return d.qid+': '+d.v+'/4'}}},datalabels:{color:'#fff',font:{size:10,weight:'bold'},formatter:(v,ctx2)=>{const d=ctx2.dataset.data[ctx2.dataIndex];return d.v}}}}});
})();

// Pathway chart
(function(){
  const ctx=document.getElementById('pathwayChart');if(!ctx||!DATA.pathways.length)return;
  const triggered=DATA.pathways.filter(p=>p.triggered>0);
  const notTriggered=DATA.pathways.filter(p=>p.triggered===0);
  new Chart(ctx,{type:'bar',data:{labels:DATA.pathways.map(p=>p.name.replace('Move to ','')),datasets:[{label:'Status',data:DATA.pathways.map(p=>p.triggered>0?1:0),backgroundColor:DATA.pathways.map(p=>p.triggered>0?C.green+'99':C.surface2),borderColor:DATA.pathways.map(p=>p.triggered>0?C.green:C.text2+'44'),borderWidth:1,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',scales:{x:{display:false},y:{grid:{display:false},ticks:{color:C.text2,font:{size:12}}}},plugins:{legend:{display:false},datalabels:{color:C.text2,anchor:'end',align:'right',font:{size:11},formatter:(v)=>v>0?'Triggered':'Not Triggered'}}}});
  // Pathway cards
  const el=document.getElementById('pathwayCards');if(!el)return;
  el.innerHTML=DATA.pathways.filter(p=>p.triggered>0).map(p=>`<div class="card" style="border-left:4px solid ${C.green}"><div class="card-title">${p.name}</div><div style="font-size:13px;color:${C.text2}">Priority: <strong style="color:${C.accent2}">${p.priority}</strong></div><div style="font-size:13px;color:${C.text2}">Effort: <strong>${p.effort}</strong></div></div>`).join('')||'<div class="card"><div class="card-title">No pathways triggered</div><p style="color:'+C.text2+'">Current architecture satisfies all pathway criteria.</p></div>';
})();
'''


# ── Individual Dashboard HTML ────────────────────────────────────────────────

def generate_individual_html(d: Portfolio) -> str:
    cat_j = json.dumps([{"name": c.name, "score": c.score} for c in d.categories])
    q_j = json.dumps([{"qid": q.qid, "title": q.title, "score": q.score, "max": q.max_score,
                        "finding": _esc(q.finding), "gap": _esc(q.gap), "rec": _esc(q.recommendation),
                        "category": q.category} for q in d.questions])
    bg_j = json.dumps([{"id": g.id, "title": g.title, "score": g.score, "affected": g.affected,
                         "rec": g.recommendation} for g in d.blocking_gaps])
    pw_j = json.dumps([{"name": pw.name, "triggered": pw.services_triggered, "total": pw.total_services,
                         "priority": pw.priority, "effort": pw.effort, "status": pw.status,
                         "goalAlignment": pw.goal_alignment} for pw in d.pathways])
    qw_j = json.dumps([{"title": q.title, "repos": q.repos, "description": q.description} for q in d.quick_wins])
    ph_j = json.dumps([{"name": p.name, "timeframe": p.timeframe, "objective": p.objective} for p in d.phases])
    summ = _esc(d.summary)

    n_pass = sum(1 for q in d.questions if q.score >= 3)
    n_warn = sum(1 for q in d.questions if q.score == 2)
    n_fail = sum(1 for q in d.questions if q.score <= 1)
    n_trig = sum(1 for pw in d.pathways if pw.services_triggered > 0)

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Agentic Readiness — {html_mod.escape(d.name)}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
''' + CSS + f'''
</head><body>
<div class="bg-glow"></div>
<div class="container">
<div class="header">
  <div class="badge">AWS Transform — Individual Agentic Readiness</div>
  <h1>{html_mod.escape(d.name)}</h1>
  <div class="subtitle">Individual Assessment · {len(d.questions)} Questions · {d.date}</div>
  <div class="goal-ctx">Goal: {html_mod.escape(d.goal)} — {html_mod.escape(d.goal_context)}</div>
</div>
<div class="nav">
  <button class="nav-btn active" onclick="showSection('overview',this)">Overview</button>
  <button class="nav-btn" onclick="showSection('findings',this)">Detailed Findings</button>
  <button class="nav-btn" onclick="showSection('gaps',this)">Critical Gaps</button>
  <button class="nav-btn" onclick="showSection('pathways',this)">Pathways</button>
  <button class="nav-btn" onclick="showSection('roadmap',this)">Roadmap</button>
</div>

<!-- OVERVIEW -->
<div id="sec-overview" class="section active">
  <div class="score-hero">
    <div class="score-ring-wrap"><canvas id="scoreRing"></canvas>
      <div class="score-center"><div class="num" id="heroScore">0</div><div class="label">of 4.0</div></div>
    </div>
    <div class="score-meta">
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--green)"></div><div class="score-meta-text"><strong>{n_pass}</strong> questions scored 3-4 (Good)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--yellow)"></div><div class="score-meta-text"><strong>{n_warn}</strong> questions scored 2 (Partial)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--red)"></div><div class="score-meta-text"><strong>{n_fail}</strong> questions scored 0-1 (Gap)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--accent)"></div><div class="score-meta-text"><strong>{len(d.blocking_gaps)}</strong> critical blockers</div></div>
    </div>
  </div>
  <div class="exec-summary card" style="margin-bottom:24px"><div class="card-title">Executive Summary</div><p style="font-size:14px;line-height:1.7;color:var(--text2)" id="execSummary"></p></div>
  <div class="grid grid-4" style="margin-bottom:24px">
    <div class="card"><div class="card-title">Overall Score</div><div class="card-value" style="color:var(--accent2)">{d.score}/4.0</div><div class="card-sub">{tier(d.score)}</div></div>
    <div class="card"><div class="card-title">Questions</div><div class="card-value" style="color:var(--accent2)">{len(d.questions)}</div><div class="card-sub">across {len(d.categories)} categories</div></div>
    <div class="card"><div class="card-title">Critical Gaps</div><div class="card-value" style="color:var(--red)">{len(d.blocking_gaps)}</div></div>
    <div class="card"><div class="card-title">Pathways Triggered</div><div class="card-value" style="color:var(--accent2)">{n_trig}</div><div class="card-sub">of {len(d.pathways)} evaluated</div></div>
  </div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Category Readiness</div><div id="catBars"></div></div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Score Distribution by Category</div><canvas id="radarChart" height="350"></canvas></div>
  <div class="card" id="quickWinsCard"><div class="card-title">\\u26A1 Quick Agent Wins</div><div id="quickWinsList" class="grid grid-2" style="gap:16px"></div></div>
</div>

<!-- FINDINGS -->
<div id="sec-findings" class="section">
  <div style="margin-bottom:24px;display:flex;gap:12px;flex-wrap:wrap">
    <button class="nav-btn active" onclick="filterQuestions('all',this)">All</button>
    <button class="nav-btn" onclick="filterQuestions('INF',this)">Infrastructure</button>
    <button class="nav-btn" onclick="filterQuestions('APP',this)">Application</button>
    <button class="nav-btn" onclick="filterQuestions('DATA',this)">Data</button>
    <button class="nav-btn" onclick="filterQuestions('SEC',this)">Security</button>
    <button class="nav-btn" onclick="filterQuestions('OPS',this)">Operations</button>
  </div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Question Heatmap</div><canvas id="heatmapChart" height="200"></canvas></div>
  <div id="questionCards" class="grid grid-2"></div>
</div>

<!-- GAPS -->
<div id="sec-gaps" class="section">
  <div class="card"><div class="card-title">\\U0001F6AB Top Priorities ({len(d.blocking_gaps)} critical gaps)</div>
    <table class="gap-table"><thead><tr><th>ID</th><th>Gap</th><th>Score</th><th>Impact</th><th>First Step</th></tr></thead>
    <tbody id="blockingTable"></tbody></table>
  </div>
</div>

<!-- PATHWAYS -->
<div id="sec-pathways" class="section">
  <div style="text-align:center;margin-bottom:32px"><h2 style="font-size:28px;font-weight:800;margin-bottom:8px">AWS Modernization Pathways</h2><p style="color:var(--text2);font-size:14px">{n_trig} of {len(d.pathways)} pathways triggered</p></div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Pathway Status</div><canvas id="pathwayChart" height="250"></canvas></div>
  <div id="pathwayCards" class="grid grid-3"></div>
</div>

<!-- ROADMAP -->
<div id="sec-roadmap" class="section">
  <div style="text-align:center;margin-bottom:32px"><h2 style="font-size:28px;font-weight:800;margin-bottom:8px">Modernization Roadmap</h2><p style="color:var(--text2);font-size:14px">{len(d.phases)} phases</p></div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Phase Timeline</div><canvas id="ganttChart" height="160"></canvas></div>
  <div id="phaseCards" class="grid grid-2"></div>
</div>

<div class="detail-overlay" id="detailOverlay" onclick="if(event.target===this)closeDetail()"><div class="detail-panel" id="detailPanel"></div></div>
</div>
<script>
const DATA={{name:"{_esc(d.name)}",score:{d.score},categories:{cat_j},questions:{q_j},blocking:{bg_j},pathways:{pw_j},quickWins:{qw_j},phases:{ph_j},summary:"{summ}"}};
''' + JS_SHARED + JS_INDIVIDUAL + '''
</script></body></html>'''


# ── Portfolio JS ─────────────────────────────────────────────────────────────

JS_PORTFOLIO = r'''
// Init portfolio dashboard
drawScoreRing(DATA.score,4);
document.getElementById('execSummary').textContent=DATA.summary;
drawCatBars(DATA.categories);
fillGapTable('blockingTable',DATA.blocking);
fillGapTable('generalTable',DATA.general);
drawPhaseCards(DATA.phases);
drawGantt(DATA.phases);
drawQuickWins(DATA.quickWins);

// Strengths & gaps lists
(function(){
  const sl=document.getElementById('strengthsList'),gl=document.getElementById('gapsList');
  if(sl)sl.innerHTML=DATA.strengths.map(s=>`<li class="strength-item">${s}</li>`).join('');
  if(gl)gl.innerHTML=DATA.commonGaps.map(g=>`<li class="gap-item">${g}</li>`).join('');
})();

// Service cards
(function(){
  const el=document.getElementById('serviceCards');if(!el)return;
  el.innerHTML=DATA.services.map(s=>{
    const tc=tierClass(s.score);
    let bars='';for(const[k,v]of Object.entries(s.categories||{})){
      bars+=`<div class="svc-bar-row"><div class="svc-bar-label">${k}</div><div class="svc-bar-track"><div class="svc-bar-fill" style="width:${v/4*100}%;background:${scColor(v)}"></div></div></div>`;
    }
    return`<div class="card svc-card ${tc}" onclick="openServiceDetail('${s.name}')"><div class="svc-name">${s.name}</div><div class="svc-score" style="color:${scColor(s.score)}">${s.score.toFixed(1)}</div>${bars}<span class="svc-priority ${s.priority.toLowerCase()}">${s.priority}</span></div>`;
  }).join('');
})();

function openServiceDetail(name){
  const s=DATA.services.find(x=>x.name===name);if(!s)return;
  let catRows='';for(const[k,v]of Object.entries(s.categories||{})){
    catRows+=`<div class="cat-row"><div class="cat-label">${k}</div><div class="cat-bar-wrap"><div class="cat-bar-track"><div class="cat-bar-fill" style="width:${v/4*100}%;background:${scColor(v)}"></div></div><div class="cat-score" style="color:${scColor(v)}">${v.toFixed(1)}/4.0</div></div></div>`;
  }
  // Find pathways for this service
  let pwHtml='';DATA.pathways.forEach(p=>{if(p.perService&&p.perService[name])pwHtml+=`<span style="display:inline-block;background:rgba(108,92,231,.15);color:${C.accent2};padding:4px 12px;border-radius:6px;font-size:12px;margin:4px">${p.name}</span>`});
  openDetail(`<h2 style="font-size:24px;font-weight:800;margin-bottom:4px">${s.name}</h2>
    <div style="font-size:36px;font-weight:800;color:${scColor(s.score)};margin-bottom:16px">${s.score.toFixed(1)} / 4.0 <span style="font-size:14px;color:${C.text2}">${tierName(s.score)}</span></div>
    <div style="margin-bottom:16px">${catRows}</div>
    ${pwHtml?'<div style="margin-top:16px"><div style="font-size:12px;font-weight:600;color:'+C.accent2+';margin-bottom:8px">PATHWAYS</div>'+pwHtml+'</div>':''}`);
}

// Radar chart
(function(){
  const ctx=document.getElementById('radarChart');if(!ctx)return;
  const catLabels=DATA.categories.map(c=>c.name);
  const datasets=DATA.services.map((s,i)=>{
    const colors=[C.accent,C.green,C.yellow,C.orange,C.red,C.blue,C.teal||'#00b894'];
    const color=colors[i%colors.length];
    return{label:s.name,data:catLabels.map(cl=>{const short=cl.substring(0,3).toUpperCase();return s.categories[short]||s.score}),borderColor:color,backgroundColor:color+'22',borderWidth:2,pointRadius:4,pointBackgroundColor:color};
  });
  new Chart(ctx,{type:'radar',data:{labels:catLabels,datasets},options:{responsive:true,maintainAspectRatio:false,scales:{r:{min:0,max:4,ticks:{stepSize:1,color:C.text2,backdropColor:'transparent'},grid:{color:'rgba(45,49,64,.5)'},pointLabels:{color:C.text2,font:{size:11}}}},plugins:{legend:{position:'bottom',labels:{color:C.text2,font:{size:11},boxWidth:12}},datalabels:{display:false}}}});
})();

// Heatmap
(function(){
  const ctx=document.getElementById('heatmapChart');if(!ctx||!DATA.services.length)return;
  const catKeys=Object.keys(DATA.services[0].categories||{});
  if(!catKeys.length)return;
  const data=[];DATA.services.forEach((s,yi)=>{catKeys.forEach((k,xi)=>{data.push({x:xi,y:yi,v:s.categories[k]||0})})});
  new Chart(ctx,{type:'scatter',data:{datasets:[{data,pointRadius:18,pointBackgroundColor:ctx2=>{const d=ctx2.raw;return d?scColor(d.v)+'cc':'transparent'},pointBorderColor:'transparent'}]},options:{responsive:true,maintainAspectRatio:false,scales:{x:{type:'linear',min:-.5,max:catKeys.length-.5,ticks:{callback:v=>catKeys[v]||'',color:C.text2},grid:{display:false}},y:{type:'linear',min:-.5,max:DATA.services.length-.5,ticks:{callback:v=>DATA.services[v]?DATA.services[v].name:'',color:C.text2},grid:{color:'rgba(45,49,64,.3)'}}},plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx2=>{const d=ctx2.raw;const s=DATA.services[d.y];const k=catKeys[d.x];return s?s.name+' / '+k+': '+d.v.toFixed(1):''}}},datalabels:{color:'#fff',font:{size:10,weight:'bold'},formatter:(v,ctx2)=>{const d=ctx2.dataset.data[ctx2.dataIndex];return d.v.toFixed(1)}}}}});
})();

// Dependencies SVG
(function(){
  const el=document.getElementById('depViz');if(!el||!DATA.deps.length){if(el)el.innerHTML='<p style="color:'+C.text2+'">No dependencies detected.</p>';return}
  const nodes=[...new Set(DATA.deps.flatMap(d=>[d.source,d.target]))];
  const w=el.clientWidth||800,h=Math.max(300,nodes.length*60);
  const cx=w/2,cy=h/2,r=Math.min(cx,cy)-60;
  const pos={};nodes.forEach((n,i)=>{const a=2*Math.PI*i/nodes.length-Math.PI/2;pos[n]={x:cx+r*Math.cos(a),y:cy+r*Math.sin(a)}});
  let svg=`<svg width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">`;
  svg+=`<defs><marker id="ah" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="${C.accent2}"/></marker></defs>`;
  DATA.deps.forEach(d=>{const s=pos[d.source],t=pos[d.target];if(!s||!t)return;const dash=d.type==='async'?'stroke-dasharray="6,4"':'';svg+=`<line x1="${s.x}" y1="${s.y}" x2="${t.x}" y2="${t.y}" stroke="${d.type==='sync'?C.accent:C.green}" stroke-width="2" ${dash} marker-end="url(#ah)"/>`});
  nodes.forEach(n=>{const p=pos[n];const svc=DATA.services.find(s=>s.name===n);const col=svc?scColor(svc.score):C.text2;svg+=`<circle cx="${p.x}" cy="${p.y}" r="24" fill="${C.surface2}" stroke="${col}" stroke-width="2"/><text x="${p.x}" y="${p.y+4}" text-anchor="middle" fill="${C.text2}" font-size="10" font-family="Inter">${n.length>12?n.substring(0,10)+'..':n}</text>`});
  svg+='</svg>';el.innerHTML=svg;
  // Dep table
  const dt=document.getElementById('depTable');if(dt)dt.innerHTML=DATA.deps.map(d=>`<tr><td>${d.source} → ${d.target}</td><td><span style="color:${d.type==='sync'?C.accent:C.green}">${d.type}</span></td><td>${d.type==='sync'?'Higher':'Lower'}</td></tr>`).join('');
})();

// Pathway chart + matrix
(function(){
  const ctx=document.getElementById('pathwayChart');if(!ctx||!DATA.pathways.length)return;
  new Chart(ctx,{type:'bar',data:{labels:DATA.pathways.map(p=>p.name.replace('Move to ','')),datasets:[{label:'Services Triggered',data:DATA.pathways.map(p=>p.triggered),backgroundColor:DATA.pathways.map(p=>p.triggered>0?C.green+'99':C.surface2),borderColor:DATA.pathways.map(p=>p.triggered>0?C.green:C.text2+'44'),borderWidth:1,borderRadius:6}]},options:{responsive:true,maintainAspectRatio:false,indexAxis:'y',scales:{x:{title:{display:true,text:'Services',color:C.text2},grid:{color:'rgba(45,49,64,.5)'},ticks:{color:C.text2}},y:{grid:{display:false},ticks:{color:C.text2,font:{size:11}}}},plugins:{legend:{display:false},datalabels:{color:C.text2,anchor:'end',align:'right',font:{size:11},formatter:(v,ctx2)=>v+'/'+DATA.pathways[ctx2.dataIndex].total}}}});
  // Cards
  const el=document.getElementById('pathwayCards');if(el)el.innerHTML=DATA.pathways.filter(p=>p.triggered>0).map(p=>`<div class="card" style="border-left:4px solid ${C.green}"><div class="card-title">${p.name}</div><div style="font-size:24px;font-weight:800;color:${C.green};margin-bottom:8px">${p.triggered}/${p.total}</div><div style="font-size:13px;color:${C.text2}">Priority: <strong style="color:${C.accent2}">${p.priority}</strong> · Effort: <strong>${p.effort}</strong></div></div>`).join('');
  // Matrix
  const mx=document.getElementById('pathwayMatrix');if(!mx||!DATA.services)return;
  let html='<table class="gap-table"><thead><tr><th>Service</th>';DATA.pathways.forEach(p=>html+=`<th style="font-size:11px">${p.name.replace('Move to ','')}</th>`);html+='</tr></thead><tbody>';
  DATA.services.forEach(s=>{html+=`<tr><td>${s.name}</td>`;DATA.pathways.forEach(p=>{const v=p.perService&&p.perService[s.name];html+=`<td style="text-align:center">${v?'✅':'—'}</td>`});html+='</tr>'});
  html+='</tbody></table>';mx.innerHTML=html;
})();
'''


# ── Portfolio Dashboard HTML ─────────────────────────────────────────────────

def generate_portfolio_html(d: Portfolio) -> str:
    nr = sum(1 for s in d.services if s.score < 1.5)
    nw = sum(1 for s in d.services if 1.5 <= s.score < 2.5)
    pa = sum(1 for s in d.services if 2.5 <= s.score < 3.5)
    ar = sum(1 for s in d.services if s.score >= 3.5)
    n = d.total_services or len(d.services)

    svc_j = json.dumps([{"name": s.name, "score": s.score, "priority": s.priority, "categories": s.categories} for s in d.services])
    cat_j = json.dumps([{"name": c.name, "score": c.score} for c in d.categories])
    bg_j = json.dumps([{"id": g.id, "title": g.title, "score": g.score, "affected": g.affected, "impact": g.impact, "rec": g.recommendation} for g in d.blocking_gaps])
    gg_j = json.dumps([{"id": g.id, "title": g.title, "score": g.score, "affected": g.affected, "impact": g.impact, "rec": g.recommendation} for g in d.general_gaps])
    dep_j = json.dumps([{"source": x.source, "target": x.target, "type": x.dtype} for x in d.deps])
    ph_j = json.dumps([{"name": p.name, "timeframe": p.timeframe, "objective": p.objective} for p in d.phases])
    pw_j = json.dumps([{"name": pw.name, "triggered": pw.services_triggered, "total": pw.total_services,
                         "priority": pw.priority, "effort": pw.effort, "perService": pw.per_service} for pw in d.pathways])
    qw_j = json.dumps([{"title": q.title, "repos": q.repos, "description": q.description} for q in d.quick_wins])
    str_j = json.dumps(d.strengths)
    cgap_j = json.dumps(d.common_gaps)
    summ = _esc(d.summary)

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Agentic Readiness — {html_mod.escape(d.name)}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
''' + CSS + f'''
</head><body>
<div class="bg-glow"></div>
<div class="container">
<div class="header">
  <div class="badge">AWS Transform — Agentic Readiness Assessment</div>
  <h1>{html_mod.escape(d.name)}</h1>
  <div class="subtitle">Portfolio Assessment · {n} Services · {d.date}</div>
  <div class="goal-ctx">Goal: {html_mod.escape(d.goal)} — {html_mod.escape(d.goal_context)}</div>
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
    <div class="score-ring-wrap"><canvas id="scoreRing"></canvas>
      <div class="score-center"><div class="num" id="heroScore">0</div><div class="label">of 4.0</div></div>
    </div>
    <div class="score-meta">
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--red)"></div><div class="score-meta-text"><strong>{nr}</strong> Not Ready (&lt;1.5)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--orange)"></div><div class="score-meta-text"><strong>{nw}</strong> Needs Work (1.5-2.4)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--yellow)"></div><div class="score-meta-text"><strong>{pa}</strong> Partial (2.5-3.4)</div></div>
      <div class="score-meta-item"><div class="score-meta-dot" style="background:var(--green)"></div><div class="score-meta-text"><strong>{ar}</strong> Agent-Ready (3.5-4.0)</div></div>
    </div>
  </div>
  <div class="exec-summary card" style="margin-bottom:24px"><div class="card-title">Executive Summary</div><p style="font-size:14px;line-height:1.7;color:var(--text2)" id="execSummary"></p></div>
  <div class="grid grid-4" style="margin-bottom:24px">
    <div class="card"><div class="card-title">Services</div><div class="card-value" style="color:var(--accent2)">{n}</div></div>
    <div class="card"><div class="card-title">Agent-Ready</div><div class="card-value" style="color:{sc(4.0) if ar > 0 else sc(0)}">{round(ar / max(n, 1) * 100)}%</div><div class="card-sub">{ar} of {n}</div></div>
    <div class="card"><div class="card-title">Blocking Gaps</div><div class="card-value" style="color:var(--red)">{len(d.blocking_gaps)}</div></div>
    <div class="card"><div class="card-title">Phases</div><div class="card-value" style="color:var(--accent2)">{len(d.phases)}</div></div>
  </div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Category Readiness</div><div id="catBars"></div></div>
  <div class="grid grid-2">
    <div class="card"><div class="card-title">Strengths</div><ul id="strengthsList" style="list-style:none;padding:0"></ul></div>
    <div class="card"><div class="card-title">Common Gaps</div><ul id="gapsList" style="list-style:none;padding:0"></ul></div>
  </div>
  <div class="card" style="margin-top:24px" id="quickWinsCard"><div class="card-title">\\u26A1 Quick Agent Wins</div><div id="quickWinsList" class="grid grid-2" style="gap:16px"></div></div>
</div>

<!-- SERVICES -->
<div id="sec-services" class="section"><div class="grid grid-2" id="serviceCards"></div></div>

<!-- CATEGORIES -->
<div id="sec-categories" class="section">
  <div class="card" style="margin-bottom:24px"><div class="card-title">Category Comparison — Radar</div><canvas id="radarChart" height="400"></canvas></div>
  <div class="card"><div class="card-title">Heatmap — Score by Service x Category</div><canvas id="heatmapChart" height="280"></canvas></div>
</div>

<!-- GAPS -->
<div id="sec-gaps" class="section">
  <div class="card" style="margin-bottom:24px"><div class="card-title">\\U0001F6AB Blocking Your Goal ({len(d.blocking_gaps)})</div>
    <table class="gap-table"><thead><tr><th>ID</th><th>Gap</th><th>Score</th><th>Services</th><th>Impact</th></tr></thead><tbody id="blockingTable"></tbody></table></div>
  <div class="card"><div class="card-title">\\u26A1 General Opportunities ({len(d.general_gaps)})</div>
    <table class="gap-table"><thead><tr><th>ID</th><th>Gap</th><th>Score</th><th>Services</th><th>Impact</th></tr></thead><tbody id="generalTable"></tbody></table></div>
</div>

<!-- PATHWAYS -->
<div id="sec-pathways" class="section">
  <div style="text-align:center;margin-bottom:32px"><h2 style="font-size:28px;font-weight:800;margin-bottom:8px">AWS Modernization Pathways</h2></div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Pathway Coverage</div><canvas id="pathwayChart" height="280"></canvas></div>
  <div id="pathwayCards" class="grid grid-3" style="margin-bottom:24px"></div>
  <div class="card"><div class="card-title">Pathway x Service Matrix</div><div id="pathwayMatrix" style="overflow-x:auto"></div></div>
</div>

<!-- DEPENDENCIES -->
<div id="sec-dependencies" class="section">
  <div class="dep-graph"><div class="card-title" style="margin-bottom:24px">Service Dependency Architecture</div><div id="depViz" style="min-height:300px"></div></div>
  <div class="card"><div class="card-title">Dependency Matrix</div><table class="gap-table"><thead><tr><th>Source → Target</th><th>Type</th><th>Risk</th></tr></thead><tbody id="depTable"></tbody></table></div>
</div>

<!-- ROADMAP -->
<div id="sec-roadmap" class="section">
  <div style="text-align:center;margin-bottom:32px"><h2 style="font-size:28px;font-weight:800;margin-bottom:8px">Modernization Roadmap</h2><p style="color:var(--text2);font-size:14px">{len(d.phases)} phases</p></div>
  <div class="card" style="margin-bottom:24px"><div class="card-title">Phase Timeline</div><canvas id="ganttChart" height="180"></canvas></div>
  <div id="phaseCards" class="grid grid-2"></div>
</div>

<div class="detail-overlay" id="detailOverlay" onclick="if(event.target===this)closeDetail()"><div class="detail-panel" id="detailPanel"></div></div>
</div>
<script>
const DATA={{name:"{_esc(d.name)}",score:{d.score},services:{svc_j},categories:{cat_j},blocking:{bg_j},general:{gg_j},deps:{dep_j},phases:{ph_j},pathways:{pw_j},quickWins:{qw_j},strengths:{str_j},commonGaps:{cgap_j},summary:"{summ}"}};
''' + JS_SHARED + JS_PORTFOLIO + '''
</script></body></html>'''


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate interactive HTML dashboard from agentic readiness reports.")
    parser.add_argument("input", help="Markdown report file or directory of reports")
    parser.add_argument("-o", "--output", help="Output HTML file (default: auto-named)")
    args = parser.parse_args()

    inp = Path(args.input)
    if inp.is_dir():
        files = sorted(inp.glob("*.md"))
        if not files:
            print(f"No .md files found in {inp}")
            sys.exit(1)
        for f in files:
            process_file(f, None)
    elif inp.is_file():
        process_file(inp, args.output)
    else:
        print(f"Not found: {inp}")
        sys.exit(1)


def process_file(md_path: Path, output: str = None):
    content = md_path.read_text(encoding="utf-8")
    d = parse_report(content)
    if not d.name:
        d.name = md_path.stem

    html = generate_html(d)
    if output:
        out = Path(output)
    else:
        out = md_path.with_suffix(".html")

    out.write_text(html, encoding="utf-8")
    rtype = "individual" if d.is_individual else "portfolio"
    print(f"✅ {rtype}: {d.name} → {out}  (score: {d.score}/4.0)")


if __name__ == "__main__":
    main()
