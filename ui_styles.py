"""
ui_styles.py — Enterprise SOC dashboard CSS theme.
Call inject_css() once at app startup.
"""

import streamlit as st

# ── Palette ───────────────────────────────────────────────────────────────────
C = {
    "bg":       "#0F1117",
    "panel":    "#161B22",
    "panel2":   "#1C2128",
    "border":   "#30363D",
    "border2":  "#484F58",
    "green":    "#00D084",
    "blue":     "#58A6FF",
    "blue2":    "#79B8FF",
    "orange":   "#FFB000",
    "critical": "#FF4D4F",
    "high":     "#FF8C00",
    "medium":   "#FFD700",
    "low":      "#00C853",
    "text":     "#F3F4F6",
    "text2":    "#C9D1D9",
    "muted":    "#8B949E",
}

_CSS = """
/* ── FONTS ──────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── RESET & BASE ────────────────────────────────────────────────────────── */
.stApp {
    background-color: #0F1117;
    font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
}
.block-container {
    padding: 0.5rem 2rem 3rem 2rem;
    max-width: 100% !important;
}

/* ── SCROLLBAR ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0F1117; }
::-webkit-scrollbar-thumb { background: #30363D; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #484F58; }

/* ── HIDE STREAMLIT CHROME ───────────────────────────────────────────────── */
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; height: 0; }
[data-testid="stDecoration"] { display: none; }

/* ── HEADER — collapsed so custom app header sits flush at top ───────────── */
[data-testid="stHeader"] {
    height: 0 !important;
    overflow: hidden !important;
}

/* ── SIDEBAR ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #161B22 !important;
    border-right: 1px solid #30363D;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
[data-testid="stSidebarContent"] {
    padding: 0 !important;
}

/* ── TABS ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid #30363D;
    gap: 0;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #8B949E;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: 10px 18px;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.01em;
    transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #C9D1D9 !important;
    background: rgba(88,166,255,0.04) !important;
}
.stTabs [aria-selected="true"] {
    color: #58A6FF !important;
    border-bottom: 2px solid #58A6FF !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }
.stTabs [data-baseweb="tab-panel"]     { padding-top: 1.25rem; }

/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 6px;
    font-size: 0.83rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    transition: all 0.18s ease;
    border: none;
}
.stButton > button[kind="primary"] {
    background: #58A6FF;
    color: #0F1117;
}
.stButton > button[kind="primary"]:hover:not(:disabled) {
    background: #79B8FF;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.25);
    transform: translateY(-1px);
}
.stButton > button[kind="primary"]:disabled {
    background: #30363D;
    color: #8B949E;
    cursor: not-allowed;
}
.stButton > button[kind="secondary"] {
    background: transparent;
    border: 1px solid #30363D !important;
    color: #C9D1D9;
}
.stButton > button[kind="secondary"]:hover:not(:disabled) {
    border-color: #58A6FF !important;
    color: #58A6FF;
    background: rgba(88,166,255,0.06) !important;
}
[data-testid="stDownloadButton"] > button {
    background: transparent;
    border: 1px solid #30363D !important;
    color: #C9D1D9;
    border-radius: 6px;
    font-size: 0.83rem;
    font-weight: 500;
    transition: all 0.18s ease;
    width: 100%;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: #00D084 !important;
    color: #00D084;
    background: rgba(0,208,132,0.06) !important;
}

/* ── INPUTS ──────────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {
    background: #1C2128 !important;
    border: 1px solid #30363D !important;
    color: #F3F4F6 !important;
    border-radius: 6px !important;
    font-size: 0.85rem;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #58A6FF !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.12) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label {
    color: #8B949E !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #1C2128 !important;
    border: 1px solid #30363D !important;
    color: #F3F4F6 !important;
    border-radius: 6px !important;
}

/* ── METRICS ─────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 14px 16px;
}
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    font-weight: 700;
    color: #F3F4F6;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── EXPANDERS ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #161B22;
    border: 1px solid #30363D !important;
    border-radius: 8px;
    margin-bottom: 6px;
}
[data-testid="stExpander"] summary {
    color: #C9D1D9 !important;
    font-size: 0.85rem;
    padding: 10px 14px;
}
[data-testid="stExpander"] summary:hover {
    background: rgba(88,166,255,0.04);
    border-radius: 8px;
}

/* ── DATAFRAME ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #30363D;
    border-radius: 8px;
    overflow: hidden;
}

/* ── FILE UPLOADER ───────────────────────────────────────────────────────── */
[data-testid="stFileUploader"] section {
    background: #1C2128 !important;
    border: 1px dashed #30363D !important;
    border-radius: 8px;
}
[data-testid="stFileUploader"] section:hover {
    border-color: #58A6FF !important;
}

/* ── ALERTS ──────────────────────────────────────────────────────────────── */
[data-testid="stInfo"]    { background: rgba(88,166,255,0.07);  border: 1px solid rgba(88,166,255,0.25);  border-radius: 6px; }
[data-testid="stWarning"] { background: rgba(255,176,0,0.07);   border: 1px solid rgba(255,176,0,0.25);   border-radius: 6px; }
[data-testid="stError"]   { background: rgba(255,77,79,0.07);   border: 1px solid rgba(255,77,79,0.25);   border-radius: 6px; }
[data-testid="stSuccess"] { background: rgba(0,208,132,0.07);   border: 1px solid rgba(0,208,132,0.25);   border-radius: 6px; }

/* ── DIVIDER ─────────────────────────────────────────────────────────────── */
hr { border-color: #30363D !important; margin: 12px 0 !important; }

/* ── SPINNER ─────────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] > div {
    border-top-color: #58A6FF !important;
}

/* ── SLIDER ──────────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stThumbValue"] {
    background: #58A6FF;
    color: #0F1117;
}

/* ── CAPTION ─────────────────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    color: #8B949E !important;
    font-size: 0.75rem !important;
}

/* ═══════════════════════════════════════════════════════════════════════════
   CUSTOM COMPONENT STYLES
   ═══════════════════════════════════════════════════════════════════════════ */

/* ── ANIMATIONS ──────────────────────────────────────────────────────────── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
}
@keyframes scanLine {
    from { background-position: 0 0; }
    to   { background-position: 0 100%; }
}
.fade-in { animation: fadeInUp 0.28s ease forwards; }

/* ── APP HEADER ──────────────────────────────────────────────────────────── */
/* ── APP HEADER ──────────────────────────────────────────────────────────── */
.soc-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0 14px 0;
    border-bottom: 2px solid #00D084;
    margin-bottom: 20px;
}
.soc-header-left  { display: flex; align-items: center; gap: 12px; }
.soc-header-logo  {
    font-size: 1.3rem;
    color: #00D084;
    font-family: 'Courier New', monospace;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1;
}
.soc-header-title {
    color: #00D084;
    font-size: 1rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: 'Courier New', monospace;
}
.soc-header-sub {
    color: #484F58;
    font-size: 0.62rem;
    margin: 3px 0 0 0;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-family: 'Courier New', monospace;
}
.soc-header-right { display: flex; align-items: center; gap: 16px; }
.soc-status-live {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #00D084;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    font-family: 'Courier New', monospace;
}
.pulse-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #00D084;
    display: inline-block;
    box-shadow: 0 0 6px #00D084;
    animation: pulseGlow 1.8s ease infinite;
}
.pulse-dot.red    { background: #FF4D4F; box-shadow: 0 0 6px #FF4D4F; }
.pulse-dot.orange { background: #FFB000; box-shadow: 0 0 6px #FFB000; }

/* ── SIDEBAR LOGO ────────────────────────────────────────────────────────── */
.sb-logo {
    padding: 14px 16px 12px 16px;
    border-bottom: 1px solid #30363D;
    margin-bottom: 0;
}
.sb-logo-title {
    color: #F3F4F6;
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin: 0;
}
.sb-logo-sub {
    color: #8B949E;
    font-size: 0.68rem;
    margin: 2px 0 0 0;
    letter-spacing: 0.02em;
}

/* ── SIDEBAR SECTION LABEL ───────────────────────────────────────────────── */
.sb-section {
    padding: 12px 16px 4px 16px;
    color: #8B949E;
    font-size: 0.63rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

/* ── KB STATUS WIDGET ────────────────────────────────────────────────────── */
.kb-widget {
    margin: 4px 0;
    padding: 10px 14px;
    background: rgba(0,208,132,0.06);
    border: 1px solid rgba(0,208,132,0.2);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.kb-widget-label { color: #8B949E; font-size: 0.72rem; font-weight: 500; }
.kb-widget-value { color: #00D084; font-size: 0.9rem; font-weight: 700; }
.kb-widget-empty {
    background: rgba(255,77,79,0.06);
    border-color: rgba(255,77,79,0.2);
}
.kb-widget-empty .kb-widget-value { color: #FF4D4F; }

/* ── SEVERITY BADGE ──────────────────────────────────────────────────────── */
.sev-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px 3px 8px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
.sev-Critical { background: rgba(255,77,79,0.12);  color: #FF4D4F; border: 1px solid rgba(255,77,79,0.35); }
.sev-High     { background: rgba(255,140,0,0.12);  color: #FF8C00; border: 1px solid rgba(255,140,0,0.35); }
.sev-Medium   { background: rgba(255,215,0,0.12);  color: #FFD700; border: 1px solid rgba(255,215,0,0.35); }
.sev-Low      { background: rgba(0,200,83,0.12);   color: #00C853; border: 1px solid rgba(0,200,83,0.35); }

/* ── KPI CARDS ───────────────────────────────────────────────────────────── */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 18px;
}
.kpi-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 14px 16px 12px 16px;
    animation: fadeInUp 0.3s ease forwards;
    transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.kpi-card:hover {
    border-color: #484F58;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.35);
}
.kpi-label {
    color: #8B949E;
    font-size: 0.66rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 5px;
}
.kpi-val {
    font-size: 1.65rem;
    font-weight: 700;
    line-height: 1;
    color: #F3F4F6;
    letter-spacing: -0.02em;
}
.kpi-sub { color: #8B949E; font-size: 0.72rem; margin-top: 5px; }

/* KPI value colour modifiers */
.kpi-blue     { color: #58A6FF; }
.kpi-green    { color: #00D084; }
.kpi-orange   { color: #FFB000; }
.kpi-critical { color: #FF4D4F; }
.kpi-high     { color: #FF8C00; }
.kpi-medium   { color: #FFD700; }
.kpi-low      { color: #00C853; }

/* Confidence bar */
.conf-bar-track {
    background: #30363D;
    border-radius: 3px;
    height: 5px;
    margin-top: 8px;
    overflow: hidden;
}
.conf-bar-fill {
    height: 5px;
    border-radius: 3px;
    background: linear-gradient(90deg, #58A6FF, #00D084);
    transition: width 0.6s cubic-bezier(0.4,0,0.2,1);
}

/* ── SECTION HEADER ──────────────────────────────────────────────────────── */
.sec-hdr {
    display: flex;
    align-items: center;
    gap: 9px;
    padding-bottom: 10px;
    border-bottom: 1px solid #30363D;
    margin-bottom: 14px;
}
.sec-hdr-icon { font-size: 0.9rem; }
.sec-hdr-title {
    color: #F3F4F6;
    font-size: 0.9rem;
    font-weight: 600;
    margin: 0;
    flex: 1;
}
.sec-hdr-count {
    background: rgba(88,166,255,0.12);
    color: #58A6FF;
    border-radius: 10px;
    padding: 1px 9px;
    font-size: 0.72rem;
    font-weight: 700;
}

/* ── EVIDENCE CARDS ──────────────────────────────────────────────────────── */
.ev-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 3px solid #30363D;
    border-radius: 0 8px 8px 0;
    padding: 11px 14px;
    margin-bottom: 7px;
    animation: fadeInUp 0.28s ease forwards;
    transition: border-left-color 0.18s, box-shadow 0.18s;
    cursor: default;
}
.ev-card:hover {
    box-shadow: 0 3px 14px rgba(0,0,0,0.3);
}
.ev-card.ev-high   { border-left-color: #00D084; }
.ev-card.ev-medium { border-left-color: #FFB000; }
.ev-card.ev-low    { border-left-color: #FF4D4F; }
.ev-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
    font-size: 0.75rem;
}
.ev-idx    { color: #8B949E; font-weight: 600; }
.ev-src    { color: #58A6FF; font-weight: 500; }
.ev-dist   { color: #8B949E; font-family: 'Courier New', monospace; }
.ev-rel    { font-size: 0.7rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; }
.ev-rel-H  { background: rgba(0,208,132,0.12);  color: #00D084; }
.ev-rel-M  { background: rgba(255,176,0,0.12);  color: #FFB000; }
.ev-rel-L  { background: rgba(255,77,79,0.12);  color: #FF4D4F; }
.ev-preview { color: #8B949E; font-size: 0.8rem; line-height: 1.5; font-family: 'Courier New', monospace; }

/* ── MITRE CARDS ─────────────────────────────────────────────────────────── */
.mitre-tactic-hdr {
    color: #8B949E;
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 14px 0 6px 0;
    border-left: 2px solid #58A6FF;
    padding-left: 8px;
    margin-bottom: 8px;
}
.mitre-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
    gap: 8px;
    margin-bottom: 6px;
}
.mitre-card {
    background: #1C2128;
    border: 1px solid #30363D;
    border-radius: 7px;
    padding: 11px 13px;
    animation: fadeInUp 0.28s ease forwards;
    transition: border-color 0.18s, transform 0.18s, background 0.18s;
    text-decoration: none;
    display: block;
}
.mitre-card:hover {
    border-color: #58A6FF;
    background: rgba(88,166,255,0.05);
    transform: translateY(-2px);
}
.mitre-id {
    color: #58A6FF;
    font-size: 0.78rem;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    margin-bottom: 4px;
}
.mitre-name {
    color: #F3F4F6;
    font-size: 0.82rem;
    font-weight: 500;
    line-height: 1.3;
}

/* ── IOC CARDS ───────────────────────────────────────────────────────────── */
.ioc-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 13px 14px;
    animation: fadeInUp 0.28s ease forwards;
    transition: border-color 0.18s;
}
.ioc-card:hover { border-color: #484F58; }
.ioc-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 9px;
}
.ioc-lbl {
    color: #8B949E;
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    display: flex;
    align-items: center;
    gap: 5px;
}
.ioc-cnt {
    background: #30363D;
    color: #F3F4F6;
    border-radius: 10px;
    padding: 1px 8px;
    font-size: 0.72rem;
    font-weight: 700;
}
.ioc-val {
    color: #00D084;
    font-family: 'Courier New', monospace;
    font-size: 0.77rem;
    padding: 2px 0;
    word-break: break-all;
    border-bottom: 1px solid rgba(48,54,61,0.6);
}
.ioc-val:last-child { border-bottom: none; }
.ioc-empty { color: #8B949E; font-size: 0.78rem; font-style: italic; }

/* ── RECOMMENDATIONS ─────────────────────────────────────────────────────── */
.rec-item {
    display: flex;
    gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid rgba(48,54,61,0.5);
    animation: fadeInUp 0.28s ease forwards;
}
.rec-item:last-child { border-bottom: none; }
.rec-num {
    background: rgba(88,166,255,0.12);
    color: #58A6FF;
    border-radius: 50%;
    min-width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
    flex-shrink: 0;
}
.rec-text { color: #C9D1D9; font-size: 0.85rem; line-height: 1.55; padding-top: 2px; }

/* ── TIMELINE ────────────────────────────────────────────────────────────── */
.tl-entry {
    display: flex;
    gap: 14px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(48,54,61,0.5);
    align-items: flex-start;
}
.tl-entry:last-child { border-bottom: none; }
.tl-time {
    color: #58A6FF;
    font-family: 'Courier New', monospace;
    font-size: 0.8rem;
    font-weight: 600;
    min-width: 72px;
    padding-top: 1px;
}
.tl-event { color: #C9D1D9; font-size: 0.85rem; line-height: 1.45; }

/* ── RIGHT PANEL ─────────────────────────────────────────────────────────── */
.rp-wrap {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 0;
    overflow: hidden;
    animation: fadeInUp 0.3s ease;
}
.rp-header {
    padding: 12px 16px;
    border-bottom: 1px solid #30363D;
    background: #1C2128;
    display: flex;
    align-items: center;
    gap: 7px;
}
.rp-header-title {
    color: #F3F4F6;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin: 0;
}
.rp-body { padding: 14px 16px; }
.rp-section { margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid #30363D; }
.rp-section:last-child { margin-bottom: 0; padding-bottom: 0; border-bottom: none; }
.rp-lbl {
    color: #8B949E;
    font-size: 0.64rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 4px;
}
.rp-val {
    color: #F3F4F6;
    font-size: 0.85rem;
    font-weight: 500;
    word-break: break-word;
}
.rp-val.muted { color: #8B949E; font-style: italic; }
.rp-export-label {
    color: #8B949E;
    font-size: 0.64rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
    display: block;
}

/* ── GRAPH TAB ───────────────────────────────────────────────────────────── */
.graph-placeholder {
    background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
    border: 1px dashed #30363D;
    border-radius: 10px;
    padding: 48px 24px;
    text-align: center;
    animation: fadeInUp 0.3s ease;
}
.graph-placeholder-icon { font-size: 2.5rem; margin-bottom: 14px; opacity: 0.5; }
.graph-placeholder-title { color: #8B949E; font-size: 0.9rem; font-weight: 600; }
.graph-placeholder-sub   { color: #484F58; font-size: 0.78rem; margin-top: 6px; }

/* ── EMPTY STATE ─────────────────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 80px 24px 60px 24px;
    animation: fadeInUp 0.4s ease;
}
.empty-icon   { font-size: 3rem; margin-bottom: 18px; opacity: 0.6; }
.empty-title  { color: #F3F4F6; font-size: 1.15rem; font-weight: 700; margin-bottom: 10px; }
.empty-desc   { color: #8B949E; font-size: 0.85rem; line-height: 1.65; max-width: 420px; margin: 0 auto; }
.empty-hint   {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 20px;
    padding: 8px 16px;
    background: rgba(88,166,255,0.07);
    border: 1px solid rgba(88,166,255,0.2);
    border-radius: 20px;
    color: #58A6FF;
    font-size: 0.78rem;
    font-weight: 500;
}

/* ── SOC CARD (generic panel) ────────────────────────────────────────────── */
.soc-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

/* ── GENERATE REPORT BUTTON AREA ─────────────────────────────────────────── */
.gen-report-area {
    background: rgba(88,166,255,0.04);
    border: 1px solid rgba(88,166,255,0.15);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
}
.gen-report-hint { color: #8B949E; font-size: 0.78rem; margin-top: 6px; }

/* ── RECENT CASES PLACEHOLDER ────────────────────────────────────────────── */
.recent-cases {
    padding: 8px 0;
}
.recent-case-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 0;
    border-bottom: 1px solid rgba(48,54,61,0.5);
    color: #8B949E;
    font-size: 0.75rem;
}
.recent-case-item:last-child { border-bottom: none; }
.recent-case-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #30363D;
    flex-shrink: 0;
}
"""


def inject_css() -> None:
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
