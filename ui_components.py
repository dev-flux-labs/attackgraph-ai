"""
ui_components.py — HTML component builders for the SOC dashboard.
All functions return HTML strings consumed by st.markdown(unsafe_allow_html=True).
No Streamlit imports — pure string builders.
"""

import html as _html
from datetime import datetime


def _e(value: str) -> str:
    """HTML-escape a string before embedding in markup."""
    return _html.escape(str(value))

# ── Severity helpers ───────────────────────────────────────────────────────

_SEV_ICONS = {
    "Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢",
}

def severity_badge(severity: str) -> str:
    icon = _SEV_ICONS.get(severity, "⚪")
    return (
        f'<span class="sev-badge sev-{severity}">'
        f'{icon} {severity}</span>'
    )


# ── App header ─────────────────────────────────────────────────────────────

def app_header(case_title: str = "", severity: str = "") -> str:
    badge = severity_badge(severity) if severity else ""
    title_part = (
        f'<span style="color:#8B949E;font-size:0.78rem;margin-right:6px;">▸</span>'
        f'<span style="color:#F3F4F6;font-size:0.85rem;font-weight:500;">{_e(case_title)}</span> {badge}'
    ) if case_title else ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""
<div class="soc-header">
  <div class="soc-header-left">
    <span class="soc-header-logo">[&gt;_]</span>
    <div>
      <p class="soc-header-title">AttackGraph AI</p>
      <p class="soc-header-sub">SOC // Threat Investigation Platform</p>
    </div>
    {f'<div style="display:flex;align-items:center;gap:6px;margin-left:18px;padding-left:18px;border-left:1px solid #30363D;">{title_part}</div>' if title_part else ''}
  </div>
  <div class="soc-header-right">
    <div class="soc-status-live">
      <span class="pulse-dot"></span> LIVE
    </div>
    <div style="color:#484F58;font-size:0.68rem;font-family:'Courier New',monospace;letter-spacing:0.06em;">{now}</div>
  </div>
</div>"""


# ── Sidebar components ─────────────────────────────────────────────────────

def sidebar_logo() -> str:
    return """
<div class="sb-logo">
  <p class="sb-logo-title">🔍 AttackGraph AI</p>
  <p class="sb-logo-sub">SOC INVESTIGATION PLATFORM</p>
</div>"""


def sidebar_section(label: str) -> str:
    return f'<div class="sb-section">{label}</div>'


def kb_status(count: int) -> str:
    cls = "kb-widget" + ("" if count > 0 else " kb-widget-empty")
    val = f"{count} chunks" if count > 0 else "EMPTY"
    return f"""
<div class="{cls}">
  <span class="kb-widget-label">Knowledge Base</span>
  <span class="kb-widget-value">{val}</span>
</div>"""


def recent_cases_placeholder() -> str:
    items = [
        ("CASE-2026-041", "Ransomware"),
        ("CASE-2026-038", "Phishing"),
        ("CASE-2026-033", "Lateral Movement"),
    ]
    rows = "".join(
        f'<div class="recent-case-item">'
        f'<span class="recent-case-dot"></span>'
        f'<span style="color:#8B949E;">{cid}</span>'
        f'<span style="color:#484F58;margin-left:auto;">{ctype}</span>'
        f'</div>'
        for cid, ctype in items
    )
    return f'<div class="recent-cases">{rows}</div>'


# ── KPI cards ──────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, color_cls: str = "", sub: str = "", icon: str = "") -> str:
    val_cls = f"kpi-val {color_cls}" if color_cls else "kpi-val"
    icon_part = f'<span>{icon}</span>' if icon else ""
    sub_part = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""
<div class="kpi-card">
  <div class="kpi-label">{icon_part}{label}</div>
  <div class="{val_cls}">{value}</div>
  {sub_part}
</div>"""


def confidence_card(confidence: int) -> str:
    color = "kpi-green" if confidence >= 70 else ("kpi-orange" if confidence >= 40 else "kpi-critical")
    bar = (
        f'<div class="conf-bar-track">'
        f'<div class="conf-bar-fill" style="width:{confidence}%"></div>'
        f'</div>'
    )
    return f"""
<div class="kpi-card">
  <div class="kpi-label">Confidence</div>
  <div class="kpi-val {color}">{confidence}%</div>
  {bar}
</div>"""


def risk_score_card(score: int) -> str:
    if score >= 80:
        color, label = "kpi-critical", "CRITICAL"
    elif score >= 60:
        color, label = "kpi-high", "HIGH"
    elif score >= 40:
        color, label = "kpi-orange", "MEDIUM"
    else:
        color, label = "kpi-low", "LOW"
    return f"""
<div class="kpi-card">
  <div class="kpi-label">Risk Score</div>
  <div class="kpi-val {color}">{score}</div>
  <div class="kpi-sub">/ 100 &nbsp;·&nbsp; {label}</div>
</div>"""


# ── Section header ─────────────────────────────────────────────────────────

def section_header(icon: str, title: str, count: str | int | None = None) -> str:
    count_span = (
        f'<span class="sec-hdr-count">{count}</span>' if count is not None else ""
    )
    return f"""
<div class="sec-hdr">
  <span class="sec-hdr-icon">{icon}</span>
  <p class="sec-hdr-title">{title}</p>
  {count_span}
</div>"""


# ── Evidence cards ─────────────────────────────────────────────────────────

def evidence_card_header(i: int, chunk: dict) -> str:
    dist = chunk["distance"]
    if dist < 1.0:
        rel_cls, rel_text, card_cls = "ev-rel ev-rel-H", "HIGH", "ev-card ev-high"
    elif dist < 1.3:
        rel_cls, rel_text, card_cls = "ev-rel ev-rel-M", "MED", "ev-card ev-medium"
    else:
        rel_cls, rel_text, card_cls = "ev-rel ev-rel-L", "LOW", "ev-card ev-low"

    preview = _e(chunk["text"][:140].replace("\n", " "))
    source = _e(chunk.get("source", "unknown"))
    return f"""
<div class="{card_cls}">
  <div class="ev-meta">
    <span class="ev-idx">#{i}</span>
    <span class="ev-src">📄 {source}</span>
    <span class="{rel_cls}">{rel_text}</span>
    <span class="ev-dist">{dist:.4f}</span>
  </div>
  <div class="ev-preview">{preview}…</div>
</div>"""


# ── MITRE cards ────────────────────────────────────────────────────────────

def mitre_tactic_header(tactic: str) -> str:
    return f'<div class="mitre-tactic-hdr">{tactic}</div>'


def mitre_cards_grid(techniques: list[dict]) -> str:
    cards = []
    for t in techniques:
        url = t["url"]
        # Only allow https://attack.mitre.org/ links to prevent URL injection
        if not url.startswith("https://attack.mitre.org/"):
            url = f"https://attack.mitre.org/techniques/{_e(t['id'])}/"
        cards.append(
            f'<a class="mitre-card" href="{_html.escape(url, quote=True)}"'
            f' target="_blank" rel="noopener noreferrer">'
            f'<div class="mitre-id">{_e(t["id"])}</div>'
            f'<div class="mitre-name">{_e(t["name"])}</div>'
            f'</a>'
        )
    return f'<div class="mitre-grid">{"".join(cards)}</div>'


# ── IOC cards ──────────────────────────────────────────────────────────────

_IOC_ICONS = {
    "IPs": "🌐", "Domains": "🔗", "MD5 Hashes": "#",
    "SHA256 Hashes": "##", "CVEs": "⚠", "File Paths": "📁",
}


def ioc_card(category: str, items: list[str]) -> str:
    icon = _IOC_ICONS.get(category, "•")
    if items:
        rows = "".join(f'<div class="ioc-val">{_e(item)}</div>' for item in items[:15])
        overflow = (
            f'<div class="ioc-empty">+ {len(items)-15} more…</div>'
            if len(items) > 15 else ""
        )
    else:
        rows = '<div class="ioc-empty">None detected</div>'
        overflow = ""
    return f"""
<div class="ioc-card">
  <div class="ioc-hdr">
    <span class="ioc-lbl">{icon} {_e(category)}</span>
    <span class="ioc-cnt">{len(items)}</span>
  </div>
  {rows}{overflow}
</div>"""


# ── Recommendation steps ───────────────────────────────────────────────────

def rec_technique_item(technique: str) -> str:
    """Single technique row with the arrow marker — escapes LLM-derived text."""
    return (
        f'<div class="rec-item">'
        f'<div class="rec-num">→</div>'
        f'<div class="rec-text">{_e(technique)}</div>'
        f'</div>'
    )


def recommendation_list(steps: list[str]) -> str:
    if not steps:
        return '<p style="color:#8B949E;font-size:0.85rem;font-style:italic;">No recommendations yet — generate a report first.</p>'
    items = "".join(
        f'<div class="rec-item">'
        f'<div class="rec-num">{i}</div>'
        f'<div class="rec-text">{_e(step)}</div>'
        f'</div>'
        for i, step in enumerate(steps, 1)
    )
    return items


# ── Right panel ────────────────────────────────────────────────────────────

def right_panel_header() -> str:
    return """
<div class="rp-wrap">
  <div class="rp-header">
    <span>📋</span>
    <p class="rp-header-title">CASE INFORMATION</p>
  </div>
  <div class="rp-body">"""


def right_panel_footer() -> str:
    return "</div></div>"


def rp_row(label: str, value: str, muted: bool = False, raw_html: bool = False) -> str:
    """
    raw_html=True: caller guarantees value is safe (e.g. severity_badge output).
    raw_html=False (default): value is escaped before rendering.
    """
    val_cls = "rp-val muted" if muted else "rp-val"
    safe_value = value if raw_html else _e(value)
    return f"""
<div class="rp-section">
  <div class="rp-lbl">{_e(label)}</div>
  <div class="{val_cls}">{safe_value}</div>
</div>"""


# ── Empty state ────────────────────────────────────────────────────────────

def empty_state() -> str:
    return """
<div class="empty-state">
  <div class="empty-icon">🛡️</div>
  <div class="empty-title">No Active Investigation</div>
  <div class="empty-desc">
    Enter an incident description in the sidebar, then click
    <strong>Investigate</strong> to search the threat intelligence
    knowledge base and generate a SOC investigation report.
  </div>
  <div class="empty-hint">
    ← Use the sidebar to start a new investigation
  </div>
</div>"""


# ── Graph placeholder ──────────────────────────────────────────────────────

def graph_placeholder_header() -> str:
    return """
<div class="graph-placeholder">
  <div class="graph-placeholder-icon">🕸️</div>
  <div class="graph-placeholder-title">Security Memory Graph</div>
  <div class="graph-placeholder-sub">Interactive visualisation coming in Phase 5 · NetworkX data available below</div>
</div>"""
