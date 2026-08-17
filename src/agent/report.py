
import html
import json
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path("reports")
INDEX_HTML = REPORTS_DIR / "index.html"


def _timestamped_path() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPORTS_DIR / f"report_{ts}.html"


# ─── Inline SVG/CSS bar chart ────────────────────────────────────────────────

def _bar_chart(data: dict, title: str, color: str = "#6366f1", max_bars: int = 10) -> str:
    """Generate an inline SVG horizontal bar chart."""
    if not data:
        return f'<div class="chart-empty">No data yet.</div>'

    items = sorted(data.items(), key=lambda x: -x[1])[:max_bars]
    max_val = max(v for _, v in items) or 1
    bar_h = 32
    gap = 8
    label_w = 200
    chart_w = 420
    total_h = len(items) * (bar_h + gap) + 40

    rows = ""
    for i, (k, v) in enumerate(items):
        y = i * (bar_h + gap) + 30
        bar_w = max(4, int(v / max_val * chart_w))
        rows += f"""
  <text x="{label_w - 8}" y="{y + bar_h//2 + 5}" text-anchor="end" font-size="12" fill="#64748b">{html.escape(str(k))}</text>
  <rect x="{label_w}" y="{y}" width="{bar_w}" height="{bar_h}" rx="4" fill="{color}" opacity="0.85"/>
  <text x="{label_w + bar_w + 6}" y="{y + bar_h//2 + 5}" font-size="12" fill="#334155" font-weight="600">{v}</text>"""

    return f"""<div class="chart-block">
  <div class="chart-title">{html.escape(title)}</div>
  <svg width="{label_w + chart_w + 60}" height="{total_h}" xmlns="http://www.w3.org/2000/svg">
    {rows}
  </svg>
</div>"""


def _accuracy_svg(initial: float, final: float) -> str:
    """Accuracy before/after visual."""
    imp = round(final - initial, 1)
    imp_color = "#22c55e" if imp >= 0 else "#ef4444"
    imp_sign = "+" if imp >= 0 else ""
    return f"""<div class="accuracy-vis">
  <div class="acc-box">
    <div class="acc-label">Initial Accuracy</div>
    <div class="acc-value" style="color:#6366f1">{initial}%</div>
    <div class="acc-sub">Evidence URL check</div>
  </div>
  <div class="acc-arrow">→</div>
  <div class="acc-box">
    <div class="acc-label">Verification</div>
    <div class="acc-value" style="color:#f59e0b">Cross-check</div>
    <div class="acc-sub">Tavily claim check</div>
  </div>
  <div class="acc-arrow">→</div>
  <div class="acc-box">
    <div class="acc-label">Final Accuracy</div>
    <div class="acc-value" style="color:#22c55e">{final}%</div>
    <div class="acc-sub">Verified claims</div>
  </div>
  <div class="acc-arrow">→</div>
  <div class="acc-box">
    <div class="acc-label">Improvement</div>
    <div class="acc-value" style="color:{imp_color}">{imp_sign}{imp} pts</div>
    <div class="acc-sub">Percentage points</div>
  </div>
</div>"""


def _workflow_svg() -> str:
    """Agent workflow diagram."""
    steps = [
        ("README", "#6366f1", "100 crawl targets"),
        ("Tavily Search", "#8b5cf6", "4 queries/app"),
        ("Web Crawler", "#a78bfa", "Top 3 sources"),
        ("Gemma 4 26B", "#c084fc", "JSON extraction"),
        ("Pydantic", "#e879f9", "Schema validation"),
        ("Verification", "#f472b6", "Claim cross-check"),
        ("Human Sample", "#fb7185", "12-app review"),
        ("Analysis", "#f87171", "Pattern detection"),
        ("HTML Report", "#fbbf24", "Case study"),
    ]
    boxes = ""
    for i, (label, color, sub) in enumerate(steps):
        x = i * 130
        boxes += f"""
  <g>
    <rect x="{x}" y="20" width="110" height="56" rx="10" fill="{color}" opacity="0.15" stroke="{color}" stroke-width="1.5"/>
    <text x="{x+55}" y="44" text-anchor="middle" font-size="12" font-weight="700" fill="{color}">{html.escape(label)}</text>
    <text x="{x+55}" y="62" text-anchor="middle" font-size="10" fill="#64748b">{html.escape(sub)}</text>
    {"" if i == len(steps)-1 else f'<text x="{x+120}" y="52" font-size="18" fill="#94a3b8">›</text>'}
  </g>"""
    total_w = len(steps) * 130
    return f"""<div class="workflow-wrap">
  <svg width="{total_w}" height="100" xmlns="http://www.w3.org/2000/svg" style="min-width:{total_w}px">
    {boxes}
  </svg>
</div>"""


# ─── Table rows ──────────────────────────────────────────────────────────────

def _buildability_badge(v: str) -> str:
    colors = {
        "ready": "#22c55e", "buildable": "#84cc16", "partial": "#f59e0b",
        "blocked": "#ef4444", "unknown": "#94a3b8",
    }
    c = colors.get(v, "#94a3b8")
    return f'<span class="badge" style="background:{c}22;color:{c};border-color:{c}55">{html.escape(v)}</span>'


def _access_badge(v: str) -> str:
    colors = {
        "self-serve-free": "#22c55e", "self-serve-trial": "#84cc16",
        "paid-gated": "#f59e0b", "partner-gated": "#f97316",
        "contact-sales": "#ef4444", "unknown": "#94a3b8",
    }
    c = colors.get(v, "#94a3b8")
    return f'<span class="badge" style="background:{c}22;color:{c};border-color:{c}55">{html.escape(v)}</span>'


def _mcp_badge(v: str) -> str:
    colors = {
        "official": "#6366f1", "community": "#8b5cf6",
        "mentioned": "#a78bfa", "none": "#94a3b8", "unknown": "#cbd5e1",
    }
    c = colors.get(v, "#94a3b8")
    return f'<span class="badge" style="background:{c}22;color:{c};border-color:{c}55">{html.escape(v)}</span>'


def _evidence_links(evidence: list) -> str:
    links = []
    for e in evidence[:3]:
        if isinstance(e, dict):
            url = e.get("url", "")
            title = e.get("title", "") or e.get("claim", "") or "Evidence"
        else:
            url, title = str(e), "Evidence"
        if url:
            links.append(f'<a href="{html.escape(url)}" target="_blank" rel="noopener" class="ev-link">{html.escape(title[:35] or "Link")}</a>')
    return " ".join(links) if links else "—"


def _table_rows(results: list[dict]) -> str:
    rows = []
    for r in results:
        conf_color = {"high": "#22c55e", "medium": "#f59e0b", "low": "#ef4444"}.get(r.get("confidence", "low"), "#94a3b8")
        review = "⚠️" if r.get("needs_manual_review") else ""
        rows.append(f"""<tr>
  <td class="num">{r['number']}</td>
  <td class="app-name"><strong>{html.escape(r.get('app',''))}</strong>{' ' + review if review else ''}</td>
  <td>{html.escape(r.get('category',''))}</td>
  <td class="desc">{html.escape(r.get('description','')[:120])}</td>
  <td>{html.escape(', '.join(r.get('auth',[]))or'—')}</td>
  <td>{_access_badge(r.get('access','unknown'))}</td>
  <td>{'✅' if r.get('api_available') else '❌'}</td>
  <td>{html.escape(', '.join(r.get('api_type',[]))or'—')}</td>
  <td>{html.escape(r.get('api_breadth','—'))}</td>
  <td>{_mcp_badge(r.get('mcp_status','unknown'))}</td>
  <td>{_buildability_badge(r.get('buildability','unknown'))}</td>
  <td class="blocker">{html.escape(r.get('blocker','') or '—')}</td>
  <td><span style="color:{conf_color};font-weight:700">{html.escape(r.get('confidence','—'))}</span></td>
  <td>{_evidence_links(r.get('evidence',[]))}</td>
</tr>""")
    return "\n".join(rows)


# ─── Easy wins cards ─────────────────────────────────────────────────────────

def _easy_wins_cards(wins: list[dict]) -> str:
    if not wins:
        return "<p>No easy wins identified in current results.</p>"
    cards = ""
    for w in wins[:12]:
        mcp_tag = ""
        if w.get("mcp_status") in ("official", "community"):
            mcp_tag = f'<span class="tag tag-mcp">MCP {w["mcp_status"]}</span>'
        breadth_tag = f'<span class="tag tag-breadth">{w.get("api_breadth","?")}</span>'
        cards += f"""<div class="win-card">
  <div class="win-num">#{w['number']}</div>
  <div class="win-name">{html.escape(w['app'])}</div>
  <div class="win-cat">{html.escape(w.get('category',''))}</div>
  <div class="win-tags">
    <span class="tag tag-access">{html.escape(w.get('access',''))}</span>
    {breadth_tag}{mcp_tag}
  </div>
</div>"""
    return f'<div class="wins-grid">{cards}</div>'


# ─── Outreach table ──────────────────────────────────────────────────────────

def _outreach_table(outreach: list[dict]) -> str:
    if not outreach:
        return "<p>No blocked/gated apps in current results.</p>"
    rows = ""
    for o in outreach[:20]:
        rows += f"""<tr>
  <td>#{o['number']}</td>
  <td><strong>{html.escape(o['app'])}</strong></td>
  <td>{html.escape(o.get('category',''))}</td>
  <td>{_access_badge(o.get('access','unknown'))}</td>
  <td>{_buildability_badge(o.get('buildability','unknown'))}</td>
  <td>{html.escape(o.get('blocker','') or '—')}</td>
</tr>"""
    return f"""<table class="mini-table">
<thead><tr><th>#</th><th>App</th><th>Category</th><th>Access</th><th>Buildability</th><th>Blocker</th></tr></thead>
<tbody>{rows}</tbody>
</table>"""


# ─── Verification detail ─────────────────────────────────────────────────────

def _verification_detail(v: dict) -> str:
    results = v.get("results", [])
    if not results:
        return "<p>No verification data.</p>"
    rows = ""
    for c in results[:30]:
        status_color = {"confirmed": "#22c55e", "corrected": "#f59e0b", "unverifiable": "#94a3b8"}.get(c.get("status", ""), "#94a3b8")
        claims_str = "; ".join(f"{k}={vv}" for k, vv in c.get("claims_checked", {}).items())
        review_flag = "⚠️" if c.get("needs_manual_review") else ""
        rows += f"""<tr>
  <td>#{c['number']}</td>
  <td>{html.escape(c.get('app',''))}{' ' + review_flag if review_flag else ''}</td>
  <td><span style="color:{status_color};font-weight:700">{html.escape(c.get('status','—'))}</span></td>
  <td>{c.get('evidence_pages_found',0)}</td>
  <td style="font-size:11px">{html.escape(claims_str or '—')}</td>
</tr>"""
    return f"""<div class="wrap">
<table class="mini-table">
<thead><tr><th>#</th><th>App</th><th>Status</th><th>Evidence URLs Live</th><th>Claims Checked</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>"""


def _human_sample_section(v: dict) -> str:
    sample = v.get("human_sample", [])
    if not sample:
        return "<p>Human review sample not yet generated.</p>"
    rows = ""
    for s in sample:
        urls = " ".join(f'<a href="{html.escape(u)}" target="_blank" class="ev-link">URL</a>' for u in s.get("evidence_urls", []) if u)
        rows += f"""<tr>
  <td>#{s['number']}</td>
  <td>{html.escape(s.get('app',''))}</td>
  <td>{html.escape(s.get('category',''))}</td>
  <td>{html.escape(s.get('buildability',''))}</td>
  <td>{html.escape(s.get('access',''))}</td>
  <td>{html.escape(s.get('mcp_status',''))}</td>
  <td>{urls or '—'}</td>
  <td style="font-size:11px;color:#f59e0b">⚠️ {html.escape(s.get('review_instructions','')[:120])}</td>
</tr>"""
    return f"""<div class="alert-box">
  <strong>⚠️ Human Review Required:</strong> The {len(sample)} apps below were selected for manual verification. 
  No human review has been performed yet. Inspect the evidence URLs to confirm the automated findings.
</div>
<div class="wrap">
<table class="mini-table">
<thead><tr><th>#</th><th>App</th><th>Category</th><th>Buildability</th><th>Access</th><th>MCP</th><th>Evidence</th><th>Instructions</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>"""


def _hits_misses(v: dict) -> str:
    hits = v.get("hits", [])
    misses = v.get("misses", [])
    hit_html = "".join(
        f'<li>#{h["number"]} <strong>{html.escape(h["app"])}</strong> — {html.escape(str(h.get("claims",{})))}</li>'
        for h in hits[:10]
    ) or "<li>No confirmed hits yet.</li>"
    miss_html = "".join(
        f'<li>#{m["number"]} <strong>{html.escape(m["app"])}</strong> — {html.escape(m.get("reason",""))}</li>'
        for m in misses[:10]
    ) or "<li>No misses.</li>"
    return f"""<div class="two-col">
  <div>
    <h3 style="color:#22c55e">✅ Hits ({len(hits)})</h3>
    <ul class="hit-miss-list">{hit_html}</ul>
  </div>
  <div>
    <h3 style="color:#ef4444">❌ Misses ({len(misses)})</h3>
    <ul class="hit-miss-list">{miss_html}</ul>
  </div>
</div>"""


def _category_table(categories: dict) -> str:
    if not categories:
        return "<p>No category data yet.</p>"
    rows = ""
    for cat, d in categories.items():
        ready = d.get("ready_buildable", 0)
        total = d.get("count", 1)
        pct = round(ready / total * 100)
        rows += f"""<tr>
  <td><strong>{html.escape(cat)}</strong></td>
  <td>{total}</td>
  <td>{d.get('api_available',0)}</td>
  <td>{ready} <span style="color:#94a3b8;font-size:11px">({pct}%)</span></td>
  <td>{dict(d.get('mcp',{})).get('official',0) + dict(d.get('mcp',{})).get('community',0)}</td>
  <td>{html.escape(max(d.get('access',{}).items(), key=lambda x:x[1])[0] if d.get('access') else '—')}</td>
</tr>"""
    return f"""<table class="mini-table">
<thead><tr><th>Category</th><th>Apps</th><th>Has API</th><th>Ready/Buildable</th><th>MCP</th><th>Dominant Access</th></tr></thead>
<tbody>{rows}</tbody>
</table>"""


# ─── CSS ─────────────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',system-ui,sans-serif;background:#f1f5f9;color:#1e293b;line-height:1.6}
a{color:#6366f1;text-decoration:none}
a:hover{text-decoration:underline}
main{max-width:1500px;margin:auto;padding:32px 24px}

/* Hero */
.hero{background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%);
  color:white;padding:60px 48px;border-radius:20px;margin-bottom:32px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-80px;right:-80px;width:300px;height:300px;
  background:radial-gradient(circle,rgba(99,102,241,.3),transparent 70%);border-radius:50%}
.hero h1{font-size:2.5rem;font-weight:800;letter-spacing:-1px;margin-bottom:12px}
.hero .sub{font-size:1.1rem;color:#a5b4fc;max-width:600px}
.hero .badge-row{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
.hero-badge{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);
  padding:6px 14px;border-radius:20px;font-size:13px;font-weight:600}

/* Metrics */
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:32px}
.metric{background:white;padding:24px;border-radius:14px;box-shadow:0 1px 3px rgba(0,0,0,.06);
  border-left:4px solid #6366f1}
.metric .label{font-size:13px;color:#64748b;font-weight:500;text-transform:uppercase;letter-spacing:.5px}
.metric .value{font-size:2rem;font-weight:800;color:#1e293b;margin-top:4px}
.metric .sub{font-size:12px;color:#94a3b8;margin-top:2px}

/* Section */
section{background:white;border-radius:16px;padding:32px;margin-bottom:24px;
  box-shadow:0 1px 3px rgba(0,0,0,.06)}
section h2{font-size:1.4rem;font-weight:700;margin-bottom:20px;color:#1e293b;
  display:flex;align-items:center;gap:10px}
section h2::before{content:'';display:inline-block;width:4px;height:24px;
  background:#6366f1;border-radius:2px}
h3{font-size:1.1rem;font-weight:600;margin:20px 0 12px;color:#334155}

/* Charts grid */
.charts-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:24px}
.chart-block{padding:20px;background:#fafbfc;border-radius:12px;border:1px solid #e2e8f0}
.chart-title{font-size:14px;font-weight:700;color:#475569;margin-bottom:12px;text-transform:uppercase;letter-spacing:.5px}
.chart-empty{color:#94a3b8;font-style:italic;font-size:14px}

/* Accuracy */
.accuracy-vis{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:12px 0}
.acc-box{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:20px 24px;text-align:center;min-width:140px}
.acc-label{font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px}
.acc-value{font-size:2rem;font-weight:800;margin:8px 0 4px}
.acc-sub{font-size:11px;color:#94a3b8}
.acc-arrow{font-size:24px;color:#94a3b8}

/* Workflow */
.workflow-wrap{overflow-x:auto;padding:12px 0}

/* Wins */
.wins-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.win-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px}
.win-num{font-size:12px;color:#94a3b8;font-weight:600}
.win-name{font-size:15px;font-weight:700;color:#1e293b;margin:4px 0 2px}
.win-cat{font-size:11px;color:#64748b;margin-bottom:8px}
.win-tags{display:flex;flex-wrap:wrap;gap:6px}
.tag{font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;border:1px solid}
.tag-access{background:#dcfce722;color:#16a34a;border-color:#bbf7d0}
.tag-breadth{background:#e0e7ff22;color:#6366f1;border-color:#c7d2fe}
.tag-mcp{background:#fdf4ff22;color:#a855f7;border-color:#e9d5ff}

/* Badges */
.badge{font-size:11px;font-weight:600;padding:2px 8px;border-radius:10px;border:1px solid;white-space:nowrap}

/* Table */
.search-bar{width:100%;padding:12px 16px;border:1px solid #e2e8f0;border-radius:10px;
  font-size:14px;margin-bottom:16px;outline:none;font-family:inherit}
.search-bar:focus{border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,.1)}
.wrap{overflow:auto;max-height:600px;border-radius:10px;border:1px solid #e2e8f0}
table{border-collapse:collapse;width:100%;font-size:12px;background:white}
th{background:#f8fafc;padding:10px 12px;border-bottom:2px solid #e2e8f0;
  text-align:left;font-weight:700;font-size:11px;color:#475569;text-transform:uppercase;
  letter-spacing:.5px;position:sticky;top:0;z-index:1}
td{padding:10px 12px;border-bottom:1px solid #f1f5f9;vertical-align:top}
tr:hover td{background:#fafbff}
.num{color:#94a3b8;font-weight:700;white-space:nowrap}
.app-name{white-space:nowrap}
.desc{max-width:200px;color:#475569}
.blocker{max-width:160px;color:#ef4444;font-size:11px}
.ev-link{font-size:11px;background:#f1f5f9;padding:2px 6px;border-radius:6px;margin-right:4px;display:inline-block}
.mini-table{width:100%;border-collapse:collapse;font-size:13px}
.mini-table th{background:#f8fafc;padding:8px 12px;border-bottom:2px solid #e2e8f0;
  font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.5px}
.mini-table td{padding:8px 12px;border-bottom:1px solid #f1f5f9}

/* Misc */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:24px}
.hit-miss-list{list-style:none;padding:0}
.hit-miss-list li{padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:13px}
.alert-box{background:#fef3c7;border:1px solid #fde68a;border-radius:10px;
  padding:14px 18px;margin-bottom:16px;font-size:13px;color:#92400e}
.findings-list{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.findings-list li{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
  padding:14px 16px;font-size:13px;display:flex;align-items:flex-start;gap:8px}
.finding-icon{font-size:18px}
.note{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:12px 16px;
  font-size:13px;color:#0369a1;margin-top:12px}

@media(max-width:900px){
  .two-col{grid-template-columns:1fr}
  .hero h1{font-size:1.8rem}
  .hero{padding:40px 28px}
}
"""


# ─── JS ──────────────────────────────────────────────────────────────────────

JS = """
function filterRows() {
  const q = document.getElementById('tbl-search').value.toLowerCase();
  document.querySelectorAll('#main-table tbody tr').forEach(row => {
    row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
  });
}
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('tbl-search').addEventListener('keyup', filterRows);
});
"""


# ─── Main report function ─────────────────────────────────────────────────────

def report(results: list[dict], analysis: dict, output: str = None) -> str:
    """Generate HTML report. Writes a timestamped file AND updates index.html. Returns the timestamped path."""
    v = analysis.get("verification", {})
    initial = v.get("initial_accuracy", 0)
    final = v.get("final_accuracy", 0)
    improvement = v.get("improvement", 0)

    count = analysis.get("count", len(results))
    api_count = analysis.get("api_available_count", 0)
    manual = analysis.get("manual_review_count", 0)
    easy_count = len(analysis.get("easy_wins", []))
    gated_count = len(analysis.get("outreach", []))
    mcp_count = sum(analysis.get("mcp", {}).get(k, 0) for k in ("official", "community"))

    # Key findings
    build = analysis.get("buildability", {})
    ready_buildable = build.get("ready", 0) + build.get("buildable", 0)

    findings = [
        ("🏗️", f"{ready_buildable} of {count} apps are ready or buildable as an AI-agent toolkit"),
        ("🔓", f"{api_count} of {count} apps expose a public API"),
        ("🤖", f"{mcp_count} apps have official or community MCP support"),
        ("🚧", f"{gated_count} apps have significant access gates (paid/partner/contact-sales)"),
        ("⭐", f"{easy_count} apps are easy-win candidates (self-serve + broad API + buildable)"),
        ("👤", f"{manual} apps require manual review due to insufficient evidence"),
    ]
    findings_html = "\n".join(
        f'<li><span class="finding-icon">{icon}</span>{html.escape(text)}</li>'
        for icon, text in findings
    )

    # Charts (6 inline SVG)
    charts = [
        _bar_chart(analysis.get("auth", {}), "Authentication Methods", "#6366f1"),
        _bar_chart(analysis.get("access", {}), "Developer Access / Gating", "#f59e0b"),
        _bar_chart(analysis.get("buildability", {}), "Buildability", "#22c55e"),
        _bar_chart(analysis.get("mcp", {}), "MCP Adoption", "#a855f7"),
        _bar_chart(dict(list(analysis.get("blockers", {}).items())[:8]), "Top Blockers", "#ef4444"),
        _bar_chart(analysis.get("api_type", {}), "API Types", "#0ea5e9"),
    ]
    charts_html = "\n".join(charts)

    imp_sign = "+" if improvement >= 0 else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Product Ops Research Agent — Case Study</title>
<meta name="description" content="Research findings from 100 AI-connected applications: API availability, authentication, MCP support, and buildability analysis.">
<style>{CSS}</style>
</head>
<body>
<main>

<!-- HERO -->
<section class="hero" style="background:linear-gradient(135deg,#0f172a,#1e1b4b,#0f172a)">
  <h1>AI Product Ops Research Agent</h1>
  <p class="sub">Automated research across 100 apps — API discovery, authentication mapping, MCP analysis, and buildability scoring for an AI-agent toolkit.</p>
  <div class="badge-row">
    <span class="hero-badge">🔍 Tavily Search</span>
    <span class="hero-badge">🤖 Gemma 4 26B</span>
    <span class="hero-badge">✅ Pydantic Validated</span>
    <span class="hero-badge">📊 {count} Apps Researched</span>
  </div>
</section>

<!-- METRICS -->
<div class="metrics">
  <div class="metric" style="border-color:#6366f1">
    <div class="label">Apps Researched</div>
    <div class="value">{count}</div>
    <div class="sub">of 100 targets</div>
  </div>
  <div class="metric" style="border-color:#22c55e">
    <div class="label">Has Public API</div>
    <div class="value">{api_count}</div>
    <div class="sub">apps with documented API</div>
  </div>
  <div class="metric" style="border-color:#f59e0b">
    <div class="label">Final Accuracy</div>
    <div class="value">{final}%</div>
    <div class="sub">{imp_sign}{improvement} pts vs initial</div>
  </div>
  <div class="metric" style="border-color:#a855f7">
    <div class="label">MCP Enabled</div>
    <div class="value">{mcp_count}</div>
    <div class="sub">official + community</div>
  </div>
  <div class="metric" style="border-color:#84cc16">
    <div class="label">Easy Wins</div>
    <div class="value">{easy_count}</div>
    <div class="sub">self-serve + broad API</div>
  </div>
  <div class="metric" style="border-color:#ef4444">
    <div class="label">Gated / Blocked</div>
    <div class="value">{gated_count}</div>
    <div class="sub">require outreach</div>
  </div>
</div>

<!-- KEY FINDINGS -->
<section>
  <h2>Key Findings</h2>
  <ul class="findings-list">{findings_html}</ul>
</section>

<!-- CHARTS -->
<section>
  <h2>Pattern Analysis</h2>
  <div class="charts-grid">{charts_html}</div>
</section>

<!-- CATEGORY ANALYSIS -->
<section>
  <h2>Category Analysis</h2>
  {_category_table(analysis.get("categories", {}))}
</section>

<!-- EASY WINS -->
<section>
  <h2>⭐ Easy Wins — Top Toolkit Candidates</h2>
  <p style="color:#64748b;margin-bottom:16px;font-size:14px">Apps with: public API + self-serve access + broad/moderate API surface + buildable/ready status.</p>
  {_easy_wins_cards(analysis.get("easy_wins", []))}
</section>

<!-- OUTREACH -->
<section>
  <h2>🚧 Blocked &amp; Gated Apps — Outreach Opportunities</h2>
  <p style="color:#64748b;margin-bottom:16px;font-size:14px">These apps require partner agreements, enterprise accounts, or sales contact before building.</p>
  {_outreach_table(analysis.get("outreach", []))}
</section>

<!-- AGENT WORKFLOW -->
<section>
  <h2>Agent Architecture</h2>
  {_workflow_svg()}
  <div class="two-col" style="margin-top:24px">
    <div>
      <h3>Python handles</h3>
      <ul style="font-size:13px;color:#475569;line-height:2;padding-left:20px">
        <li>Parsing README for 100 crawl targets</li>
        <li>Tavily multi-query search (4 queries/app)</li>
        <li>HTTP crawling with fallback extraction</li>
        <li>Text cleaning and length limiting</li>
        <li>Persisting results after each app</li>
        <li>Resume from last saved state</li>
        <li>Verification and accuracy calculation</li>
        <li>Pattern analysis and report generation</li>
      </ul>
    </div>
    <div>
      <h3>Gemma 4 26B handles</h3>
      <ul style="font-size:13px;color:#475569;line-height:2;padding-left:20px">
        <li>Reading combined source text</li>
        <li>Extracting structured facts as JSON</li>
        <li>Classifying authentication methods</li>
        <li>Determining developer access level</li>
        <li>Assessing API availability and breadth</li>
        <li>Detecting MCP support</li>
        <li>Scoring buildability and confidence</li>
      </ul>
    </div>
  </div>
  <div class="note">
    <strong>Model:</strong> Self-hosted Gemma 4 26B via OpenAI-compatible HTTP endpoint (ngrok). 
    Python handles all I/O; Gemma only performs structured text extraction.
  </div>
</section>

<!-- VERIFICATION -->
<section>
  <h2>Automated Verification</h2>
  {_verification_detail(v)}
</section>

<!-- HUMAN SAMPLE -->
<section>
  <h2>Human Review Sample</h2>
  {_human_sample_section(v)}
</section>

<!-- ACCURACY -->
<section>
  <h2>Accuracy — Before vs After Verification</h2>
  {_accuracy_svg(initial, final)}
  <p style="font-size:13px;color:#64748b;margin-top:16px">
    <strong>Initial accuracy:</strong> measured by checking whether evidence URLs return live content.<br>
    <strong>Final accuracy:</strong> measured by cross-checking key claims (access, buildability) via a secondary Tavily search.<br>
    All numbers are derived from actual pipeline results, not invented.
  </p>
</section>

<!-- HITS & MISSES -->
<section>
  <h2>Hits &amp; Misses</h2>
  {_hits_misses(v)}
</section>

<!-- 100-APP TABLE -->
<section>
  <h2>100-App Research Matrix</h2>
  <input id="tbl-search" class="search-bar" type="text" placeholder="Filter by app, category, access, buildability…">
  <div class="wrap">
    <table id="main-table">
      <thead><tr>
        <th>#</th><th>App</th><th>Category</th><th>Description</th>
        <th>Auth</th><th>Access</th><th>API</th><th>API Type</th><th>Breadth</th>
        <th>MCP</th><th>Buildability</th><th>Blocker</th><th>Confidence</th><th>Evidence</th>
      </tr></thead>
      <tbody>
        {_table_rows(results)}
      </tbody>
    </table>
  </div>
</section>

<!-- METHODOLOGY -->
<section>
  <h2>Methodology</h2>
  <p style="font-size:14px;color:#475569;line-height:1.8">
    <strong>Data collection:</strong> For each of the 100 apps from the README, four targeted Tavily searches were run 
    (API docs, authentication, pricing/access, MCP). The top 8 search results were crawled; 
    the first 3 with readable content were combined (up to ~12,000 chars each).<br><br>
    <strong>Extraction:</strong> The combined text was sent to self-hosted Gemma 4 26B via an OpenAI-compatible HTTP endpoint. 
    Gemma was prompted to return only JSON matching the Pydantic schema. Up to 3 retries were attempted on parse failure.<br><br>
    <strong>Validation:</strong> All responses were validated with Pydantic. Apps that failed all retries were marked 
    <code>needs_manual_review=True</code>.<br><br>
    <strong>Verification:</strong> Evidence URLs were checked for liveness. Key claims (access, buildability) were 
    cross-checked via a secondary Tavily search to determine confirmed / unverifiable status.<br><br>
    <strong>Honesty:</strong> No research data, evidence, or accuracy numbers were fabricated. 
    Where sources were inaccessible, the result reflects that limitation.
  </p>
</section>

</main>
<script>{JS}</script>
</body>
</html>"""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Always create a new timestamped file
    ts_path = _timestamped_path()
    ts_path.write_text(page, encoding="utf-8")

    # Also update the always-latest index.html
    INDEX_HTML.write_text(page, encoding="utf-8")

    # If caller specified a custom output path, write there too
    if output and output not in (str(INDEX_HTML), str(ts_path)):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(page, encoding="utf-8")

    return str(ts_path)
