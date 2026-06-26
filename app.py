"""
app.py — AttackGraph AI SOC Dashboard.
UI layer only. All backend imports are unchanged from previous phases.
Run with: streamlit run app.py
"""

import re
import subprocess
import time
import urllib.request
import pandas as pd
from datetime import datetime

import streamlit as st

# ── Backend (DO NOT MODIFY) ────────────────────────────────────────────────
from file_parser import parse_file
from graph import SecurityGraph, ENTITY_TYPES
from ioc_extract import extract as extract_iocs
from ingest import chunk_text
from llm import generate_report
from mitre import techniques_from_texts
from rag import collection_size, ingest_chunks, retrieve
from report import build_report
from template_rag import ensure_templates_ingested, get_relevant_template
from export_md import to_markdown, filename as md_filename
from export_pdf import to_pdf, filename as pdf_filename

# ── UI layer ───────────────────────────────────────────────────────────────
from ui_styles import inject_css
import ui_components as ui
from graph_viz import build_pyvis_html, legend_html

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AttackGraph AI — SOC Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── One-time process initialisation ───────────────────────────────────────

@st.cache_resource
def _start_ollama() -> str:
    """Start ollama serve if it isn't already running. Returns a status string."""
    try:
        urllib.request.urlopen("http://localhost:11434", timeout=2)
        return "already running"
    except Exception:
        pass  # not up yet — start it

    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait up to 8 s for the server to accept connections
    for _ in range(16):
        time.sleep(0.5)
        try:
            urllib.request.urlopen("http://localhost:11434", timeout=1)
            return "started"
        except Exception:
            continue
    return "timeout"

@st.cache_resource
def _init_templates():
    ensure_templates_ingested()

@st.cache_resource
def _load_graph() -> SecurityGraph:
    return SecurityGraph.load()

_start_ollama()
_init_templates()

# ── Score helpers ──────────────────────────────────────────────────────────

def _confidence(results: list[dict]) -> int:
    if not results:
        return 0
    avg = sum(r["distance"] for r in results) / len(results)
    return max(0, int((1.5 - min(avg, 1.5)) / 1.5 * 100))

def _risk_score(severity: str, mitre_count: int, ioc_count: int, conf: int) -> int:
    base = {"Critical": 90, "High": 70, "Medium": 50, "Low": 30}.get(severity, 50)
    return min(100, base + min(mitre_count * 2, 15) + min(ioc_count, 10) + conf // 20)

# ── Upload helper ──────────────────────────────────────────────────────────

def _ingest_uploads(uploaded_files) -> None:
    for uf in uploaded_files:
        try:
            raw = parse_file(uf.name, uf.read())
            if not raw.strip():
                st.warning(f"{uf.name}: empty — skipped.")
                continue
            chunks = chunk_text(raw)
            doc_id = re.sub(r"[^\w.-]", "_", uf.name)
            ext = uf.name.rsplit(".", 1)[-1].lower() if "." in uf.name else "unknown"
            n = ingest_chunks(chunks, source=uf.name, file_type=ext, doc_id=doc_id)
            st.success(f"✓ {uf.name}: {n} chunk(s) ingested")
        except ValueError as e:
            st.error(f"{uf.name}: {e}")
        except Exception as e:
            st.error(f"{uf.name}: unexpected error — {e}")

# ── Pre-compute values needed in sidebar ──────────────────────────────────
kb_size = collection_size()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(ui.sidebar_logo(), unsafe_allow_html=True)

    # ── New Investigation ────────────────────────────────────────────────
    st.markdown(ui.sidebar_section("New Investigation"), unsafe_allow_html=True)

    case_title = st.text_input(
        "Case Title",
        placeholder="e.g. CASE-2026-042 — Ransomware on PROD-DB",
        key="case_title",
    )
    severity = st.selectbox(
        "Severity",
        ["Critical", "High", "Medium", "Low"],
        index=1,
        key="severity",
    )
    query = st.text_area(
        "Incident Description",
        height=110,
        placeholder="Paste IOCs, log snippets, or describe the incident…",
        key="query_input",
    )

    top_k = st.slider("Evidence chunks", min_value=1, max_value=10, value=5)
    model_name = st.text_input(
        "Ollama model",
        value="llama3.2",
        help="Run `ollama pull <model>` to download.",
    )

    col_inv, col_clr = st.columns([5, 2])
    with col_inv:
        investigate = st.button(
            "⚡ Investigate",
            type="primary",
            use_container_width=True,
            disabled=(kb_size == 0),
        )
    with col_clr:
        if st.button("✕ Clear", use_container_width=True):
            for k in ("results", "report", "report_obj", "mitre_techniques",
                      "iocs", "timeline", "last_query", "model_name", "analyst_notes"):
                st.session_state.pop(k, None)
            st.rerun()

    # ── Example queries ──────────────────────────────────────────────────
    st.divider()
    st.markdown(ui.sidebar_section("Quick Scenarios"), unsafe_allow_html=True)
    examples = [
        ("🎣", "Phishing + MFA bypass"),
        ("🔒", "Ransomware shadow copy deletion"),
        ("↔️",  "Lateral movement via PsExec"),
        ("⚡", "Mimikatz pass-the-hash"),
        ("📡", "Cobalt Strike C2 beacon"),
    ]
    for icon, label in examples:
        if st.button(f"{icon} {label}", use_container_width=True, key=f"ex_{label}"):
            st.session_state["query_input"] = label
            for k in ("results", "report", "report_obj", "mitre_techniques", "iocs", "timeline"):
                st.session_state.pop(k, None)

    # ── Upload Evidence ──────────────────────────────────────────────────
    st.divider()
    st.markdown(ui.sidebar_section("Upload Evidence"), unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop files here",
        type=["txt", "log", "csv", "json"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded:
        if st.button("⬆ Ingest files", use_container_width=True):
            with st.spinner("Ingesting…"):
                _ingest_uploads(uploaded)
            st.rerun()

    # ── KB Status ────────────────────────────────────────────────────────
    st.divider()
    st.markdown(ui.sidebar_section("Knowledge Base"), unsafe_allow_html=True)
    st.markdown(ui.kb_status(kb_size), unsafe_allow_html=True)
    if kb_size == 0:
        st.caption("Run `python ingest.py` to populate the knowledge base.")

    # ── Recent Cases (placeholder) ───────────────────────────────────────
    st.divider()
    st.markdown(ui.sidebar_section("Recent Cases"), unsafe_allow_html=True)
    st.markdown(ui.recent_cases_placeholder(), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# INVESTIGATE ACTION
# ══════════════════════════════════════════════════════════════════════════════
if investigate:
    if not query.strip():
        st.warning("Enter an incident description first.")
    else:
        with st.spinner("Searching threat intelligence knowledge base…"):
            try:
                results = retrieve(query, top_k=top_k)
                st.session_state.update({
                    "results": results,
                    "last_query": query,
                    "model_name": model_name,
                })
                combined = query + " " + " ".join(c["text"] for c in results)
                st.session_state["iocs"] = extract_iocs(combined)

                # Auto-extract timestamps from query for timeline seed
                ts_pat = re.compile(
                    r"\b(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?Z?|"
                    r"\d{1,2}:\d{2}(?::\d{2})?)\b"
                )
                existing = {e["time"] for e in st.session_state.get("timeline", [])}
                auto = [
                    {"time": m.group(), "event": ""}
                    for m in ts_pat.finditer(query)
                    if m.group() not in existing
                ]
                st.session_state["timeline"] = st.session_state.get("timeline", []) + auto

                for k in ("report", "report_obj", "mitre_techniques"):
                    st.session_state.pop(k, None)

            except Exception as e:
                st.error(f"Retrieval error: {e}")
                st.session_state.pop("results", None)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════
has_results = "results" in st.session_state and st.session_state["results"]

# App header (always visible)
st.markdown(
    ui.app_header(
        case_title=st.session_state.get("case_title", ""),
        severity=st.session_state.get("severity", ""),
    ),
    unsafe_allow_html=True,
)

if not has_results:
    st.markdown(ui.empty_state(), unsafe_allow_html=True)
    st.stop()

# ── Data aliases ──────────────────────────────────────────────────────────
results    = st.session_state["results"]
last_query = st.session_state.get("last_query", "")
saved_model = st.session_state.get("model_name", model_name)
iocs       = st.session_state.get("iocs", {})
timeline   = st.session_state.get("timeline", [])
report_obj = st.session_state.get("report_obj")
mitre_techniques = st.session_state.get("mitre_techniques", [])

conf       = _confidence(results)
sev        = st.session_state.get("severity", "High")
ioc_total  = sum(len(v) for v in iocs.values())

# ── Layout: main workspace + right panel ──────────────────────────────────
ws_col, rp_col = st.columns([7, 3], gap="medium")

# ══════════════════════════════════════════════════════════════════════════════
# TABS — Main Workspace
# ══════════════════════════════════════════════════════════════════════════════
with ws_col:
    tab_ov, tab_ev, tab_mitre, tab_rec, tab_tl, tab_graph = st.tabs([
        "  Overview  ",
        "  Evidence  ",
        "  MITRE ATT&CK  ",
        "  Recommendations  ",
        "  Timeline  ",
        "  Graph  ",
    ])

    # ── TAB 1: OVERVIEW ───────────────────────────────────────────────────
    with tab_ov:
        risk = _risk_score(sev, len(mitre_techniques), ioc_total, conf)

        # ── KPI row ───────────────────────────────────────────────────────
        sev_cls = f"kpi-{sev.lower()}"
        kpi_html = (
            '<div class="kpi-row">'
            + ui.kpi_card("Severity",    sev,               sev_cls,  icon="🚨")
            + ui.risk_score_card(risk)
            + ui.confidence_card(conf)
            + ui.kpi_card("Evidence",    str(len(results)), "kpi-blue", sub="chunks retrieved", icon="📋")
            + ui.kpi_card("IOCs Found",  str(ioc_total),    "kpi-orange" if ioc_total else "kpi-low", icon="🔎")
            + ui.kpi_card("MITRE",       str(len(mitre_techniques)), "kpi-blue", sub="techniques", icon="🛡")
            + ui.kpi_card("Hosts",       str(len(iocs.get("IPs", []) + iocs.get("Domains", []))), icon="🖥")
            + ui.kpi_card("Timeline",    str(len([e for e in timeline if e.get("event")])), sub="events", icon="🕐")
            + '</div>'
        )
        st.markdown(kpi_html, unsafe_allow_html=True)

        # ── Generate Report ───────────────────────────────────────────────
        st.markdown(
            '<p style="color:#8B949E;font-size:0.72rem;font-weight:700;'
            'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">'
            '🤖 LLM Report Generation</p>',
            unsafe_allow_html=True,
        )
        if st.button("Generate Investigation Report", type="primary"):
            try:
                tmpl = get_relevant_template(last_query)
                if tmpl:
                    tname, ttext = tmpl
                    st.caption(f"Template applied: **{tname}**")
                else:
                    ttext = None

                with st.spinner("Generating SOC investigation report…"):
                    _raw = st.write_stream(
                        generate_report(last_query, results, model=saved_model, template=ttext)
                    )
                full_text = _raw if isinstance(_raw, str) else ""
                st.session_state["report"] = full_text

                context_text = " ".join(c["text"] for c in results)
                techniques = techniques_from_texts(context_text, full_text)
                st.session_state["mitre_techniques"] = techniques

                robj = build_report(
                    llm_text=full_text,
                    case_title=st.session_state.get("case_title", ""),
                    severity=sev,
                    query=last_query,
                    timeline=st.session_state.get("timeline", []),
                    analyst_notes=st.session_state.get("analyst_notes", ""),
                    evidence_chunks=results,
                    mitre_techniques=techniques,
                )
                st.session_state["report_obj"] = robj

                mem = _load_graph()
                new_edges = mem.populate_from_investigation(
                    case_title=st.session_state.get("case_title", "Unnamed"),
                    iocs=iocs,
                    mitre_techniques=techniques,
                    query=last_query,
                    report_text=full_text,
                )
                mem.save()
                if new_edges:
                    st.caption(f"Memory graph updated: +{new_edges} relationship(s)")

                st.rerun()

            except ConnectionError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"LLM error: {e}")

        # ── Executive Summary ─────────────────────────────────────────────
        if report_obj and report_obj.incident_summary:
            st.markdown(
                ui.section_header("📊", "Executive Summary"),
                unsafe_allow_html=True,
            )
            # Render LLM text via st.markdown (no unsafe_allow_html) to avoid XSS
            st.markdown(report_obj.incident_summary)
        elif "report" in st.session_state:
            st.markdown(
                ui.section_header("📊", "Full Report"),
                unsafe_allow_html=True,
            )
            st.markdown(st.session_state["report"])

    # ── TAB 2: EVIDENCE ───────────────────────────────────────────────────
    with tab_ev:
        # Evidence cards
        st.markdown(
            ui.section_header("📋", "Retrieved Evidence", len(results)),
            unsafe_allow_html=True,
        )
        for i, chunk in enumerate(results, 1):
            st.markdown(ui.evidence_card_header(i, chunk), unsafe_allow_html=True)
            with st.expander("View full text", expanded=False):
                st.markdown(chunk["text"])

        # IOC Summary
        st.markdown("---")
        st.markdown(
            ui.section_header("🔎", "Extracted IOCs", ioc_total),
            unsafe_allow_html=True,
        )
        active_cats = [(k, v) for k, v in iocs.items() if v]
        empty_cats  = [(k, v) for k, v in iocs.items() if not v]

        if active_cats:
            cols = st.columns(min(len(active_cats), 3))
            for col, (cat, items) in zip(cols, active_cats):
                with col:
                    st.markdown(ui.ioc_card(cat, items), unsafe_allow_html=True)
            # Remaining categories beyond 3 columns
            for cat, items in active_cats[3:]:
                st.markdown(ui.ioc_card(cat, items), unsafe_allow_html=True)
        if empty_cats:
            with st.expander("Categories with no findings"):
                st.write(", ".join(k for k, _ in empty_cats))
        if not active_cats:
            st.info("No IOCs detected in the query or retrieved context.")

    # ── TAB 3: MITRE ATT&CK ──────────────────────────────────────────────
    with tab_mitre:
        st.markdown(
            ui.section_header("🛡", "MITRE ATT&CK Techniques", len(mitre_techniques)),
            unsafe_allow_html=True,
        )
        if not mitre_techniques:
            st.info("Generate a report to populate MITRE technique mappings.")
        else:
            by_tactic: dict[str, list] = {}
            for t in mitre_techniques:
                by_tactic.setdefault(t["tactic"], []).append(t)
            for tactic, techs in by_tactic.items():
                st.markdown(ui.mitre_tactic_header(tactic), unsafe_allow_html=True)
                st.markdown(ui.mitre_cards_grid(techs), unsafe_allow_html=True)

    # ── TAB 4: RECOMMENDATIONS ────────────────────────────────────────────
    with tab_rec:
        steps = report_obj.recommended_steps if report_obj else []
        st.markdown(
            ui.section_header("✅", "Recommended Next Steps", len(steps) or None),
            unsafe_allow_html=True,
        )
        st.markdown(ui.recommendation_list(steps), unsafe_allow_html=True)

        if report_obj and report_obj.attack_techniques:
            st.markdown("---")
            st.markdown(
                ui.section_header("⚔️", "Likely Attack Techniques"),
                unsafe_allow_html=True,
            )
            for t in report_obj.attack_techniques:
                # Use ui helper — _e() escapes LLM-derived text before HTML insertion
                st.markdown(
                    ui.rec_technique_item(t),
                    unsafe_allow_html=True,
                )

    # ── TAB 5: TIMELINE ───────────────────────────────────────────────────
    with tab_tl:
        st.markdown(
            ui.section_header("🕐", "Incident Timeline"),
            unsafe_allow_html=True,
        )
        st.caption("Auto-extracted timestamps are pre-filled. Edit or add entries below.")

        tl: list[dict] = st.session_state.get("timeline", [])
        to_del = []
        for idx, entry in enumerate(tl):
            c_time, c_event, c_del = st.columns([2, 7, 1])
            with c_time:
                tl[idx]["time"] = st.text_input(
                    "Time", value=entry.get("time", ""),
                    key=f"tl_t_{idx}", label_visibility="collapsed",
                    placeholder="HH:MM",
                )
            with c_event:
                tl[idx]["event"] = st.text_input(
                    "Event", value=entry.get("event", ""),
                    key=f"tl_e_{idx}", label_visibility="collapsed",
                    placeholder="Describe the event…",
                )
            with c_del:
                if st.button("🗑", key=f"tl_d_{idx}"):
                    to_del.append(idx)

        for idx in reversed(to_del):
            tl.pop(idx)
        st.session_state["timeline"] = tl

        if st.button("＋ Add event", key="tl_add"):
            st.session_state["timeline"].append({"time": "", "event": ""})
            st.rerun()

    # ── TAB 6: GRAPH ──────────────────────────────────────────────────────
    with tab_graph:
        g = _load_graph()
        n_nodes = g.G.number_of_nodes()
        n_edges = g.G.number_of_edges()

        st.markdown(
            ui.section_header("🕸", "Security Memory Graph",
                              f"{n_nodes} entities · {n_edges} relationships"),
            unsafe_allow_html=True,
        )

        if n_nodes == 0:
            st.info("No graph data yet — run an investigation and generate a report to populate the memory graph.")
        else:
            # ── Interactive pyvis canvas ──────────────────────────────────
            st.markdown(legend_html(), unsafe_allow_html=True)
            graph_html = build_pyvis_html(g.G, height=560)
            st.components.v1.html(graph_html, height=575, scrolling=False)

            # ── Entity type summary metrics ───────────────────────────────
            st.markdown("---")
            summary = g.summary()
            m_cols = st.columns(len(ENTITY_TYPES))
            for col, etype in zip(m_cols, ENTITY_TYPES):
                col.metric(etype.capitalize(), summary.get(etype, 0))

            # ── Entity / relationship tables ──────────────────────────────
            st.markdown("---")
            g_col_a, g_col_b = st.columns(2)
            with g_col_a:
                st.markdown("**Entities**")
                st.dataframe(pd.DataFrame(g.all_nodes()), use_container_width=True, hide_index=True)
            with g_col_b:
                st.markdown("**Relationships**")
                st.dataframe(pd.DataFrame(g.all_edges()), use_container_width=True, hide_index=True)

        if st.button("Clear memory graph", key="clear_graph"):
            g.G.clear()
            g.save()
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL
# ══════════════════════════════════════════════════════════════════════════════
with rp_col:
    st.markdown(ui.right_panel_header(), unsafe_allow_html=True)

    # Case metadata
    title_val = st.session_state.get("case_title") or "—"
    sev_val   = st.session_state.get("severity", "—")
    st.markdown(
        ui.rp_row("CASE TITLE", title_val, muted=(title_val == "—"))
        + ui.rp_row("SEVERITY", f'<span style="margin-right:0">{ui.severity_badge(sev_val)}</span>', raw_html=True)
        + ui.rp_row("STATUS",
            '<span class="pulse-dot" style="margin-right:6px;"></span>'
            '<span style="color:#00D084;font-size:0.85rem;">Active Investigation</span>',
            raw_html=True)
        + ui.rp_row("GENERATED",
            datetime.now().strftime("%Y-%m-%d %H:%M") if report_obj else "—",
            muted=(report_obj is None))
        + ui.rp_row("EVIDENCE", f"{len(results)} chunks retrieved")
        + ui.rp_row("IOCs DETECTED", str(ioc_total)),
        unsafe_allow_html=True,
    )
    st.markdown(ui.right_panel_footer(), unsafe_allow_html=True)

    # Analyst Notes
    st.markdown("---")
    st.markdown(
        '<p style="color:#8B949E;font-size:0.68rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;">Analyst Notes</p>',
        unsafe_allow_html=True,
    )
    analyst_notes = st.text_area(
        "Analyst Notes",
        value=st.session_state.get("analyst_notes", ""),
        height=100,
        placeholder="Add observations, hypotheses, or next actions…",
        key="analyst_notes",
        label_visibility="collapsed",
    )

    # Export
    if report_obj:
        report_obj.analyst_notes = analyst_notes
        report_obj.timeline = st.session_state.get("timeline", [])

        st.markdown("---")
        st.markdown(
            '<span class="rp-export-label">Export Report</span>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇ Download Markdown",
            data=to_markdown(report_obj),
            file_name=md_filename(report_obj),
            mime="text/markdown",
            use_container_width=True,
        )
        st.download_button(
            "⬇ Download PDF",
            data=to_pdf(report_obj),
            file_name=pdf_filename(report_obj),
            mime="application/pdf",
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    '<div style="border-top:1px solid #30363D;margin-top:32px;padding-top:12px;'
    'display:flex;justify-content:space-between;align-items:center;">'
    '<span style="color:#484F58;font-size:0.72rem;">'
    'AttackGraph AI &nbsp;·&nbsp; SOC Investigation Platform</span>'
    '<span style="color:#484F58;font-size:0.72rem;font-family:\'Courier New\',monospace;">'
    'ChromaDB &nbsp;·&nbsp; SentenceTransformers &nbsp;·&nbsp; Ollama &nbsp;·&nbsp; NetworkX</span>'
    '</div>',
    unsafe_allow_html=True,
)
