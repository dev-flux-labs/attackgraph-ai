"""
app.py — AttackGraph AI SOC dashboard.
Run with: streamlit run app.py
"""

import re
from datetime import datetime

import streamlit as st

from file_parser import parse_file
from ioc_extract import extract as extract_iocs
from ingest import chunk_text
from llm import generate_report
from mitre import techniques_from_texts
from rag import collection_size, ingest_chunks, retrieve
from report import build_report
from export_md import to_markdown, filename as md_filename
from export_pdf import to_pdf, filename as pdf_filename

st.set_page_config(
    page_title="AttackGraph AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Severity colours (used in badge and header) ---
SEVERITY_COLORS = {
    "Critical": "#FF4B4B",
    "High":     "#FF8C00",
    "Medium":   "#FFD700",
    "Low":      "#00C853",
}
SEVERITY_ICONS = {
    "Critical": "🔴",
    "High":     "🟠",
    "Medium":   "🟡",
    "Low":      "🟢",
}


def _severity_badge(severity: str) -> str:
    color = SEVERITY_COLORS.get(severity, "#888888")
    icon = SEVERITY_ICONS.get(severity, "⚪")
    return (
        f'<span style="background:{color};color:#000;font-weight:bold;'
        f'padding:3px 10px;border-radius:12px;font-size:0.85rem;">'
        f'{icon} {severity}</span>'
    )


def _ingest_uploads(uploaded_files) -> None:
    """Parse, chunk, embed, and store each uploaded file. Shows per-file feedback."""
    import re as _re
    for uf in uploaded_files:
        try:
            raw = parse_file(uf.name, uf.read())
            if not raw.strip():
                st.warning(f"{uf.name}: file is empty — skipped.")
                continue
            chunks = chunk_text(raw)
            # Sanitise filename for use as a ChromaDB document ID
            doc_id = _re.sub(r"[^\w.-]", "_", uf.name)
            ext = uf.name.rsplit(".", 1)[-1].lower() if "." in uf.name else "unknown"
            n = ingest_chunks(chunks, source=uf.name, file_type=ext, doc_id=doc_id)
            st.success(f"{uf.name}: {n} chunk(s) ingested.")
        except ValueError as e:
            st.error(f"{uf.name}: {e}")
        except Exception as e:
            st.error(f"{uf.name}: unexpected error — {e}")


# --- Sidebar ---
with st.sidebar:
    st.title("🔍 AttackGraph AI")
    st.caption("SOC Incident Investigation Platform")
    st.divider()

    kb_size = collection_size()
    if kb_size == 0:
        st.error("Knowledge base empty — run `python ingest.py` first.")
    else:
        st.metric("Knowledge Base", f"{kb_size} chunks",
                  help="Threat intel chunks indexed in ChromaDB")

    st.divider()
    st.subheader("Upload Files")
    uploaded_files = st.file_uploader(
        "Add to knowledge base",
        type=["txt", "log", "csv", "json"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="Files are chunked, embedded, and stored in ChromaDB.",
    )
    if uploaded_files:
        if st.button("Ingest uploaded files", use_container_width=True, type="secondary"):
            with st.spinner("Ingesting…"):
                _ingest_uploads(uploaded_files)
            st.rerun()

    st.divider()
    st.subheader("Settings")
    top_k = st.slider("Results to retrieve", min_value=1, max_value=10, value=5)
    model_name = st.text_input(
        "Ollama model", value="llama3.2",
        help="Run `ollama pull <model>` to download a model.",
    )

    st.divider()
    st.subheader("Example queries")
    examples = [
        "Suspicious PowerShell execution and lateral movement",
        "Ransomware deleting shadow copies",
        "Phishing email bypassing MFA",
        "Mimikatz pass-the-hash attack",
        "Cobalt Strike C2 beacon traffic",
    ]
    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state["query_input"] = example
            for key in ("results", "report", "report_obj", "mitre_techniques", "iocs", "timeline"):
                st.session_state.pop(key, None)

    if "results" in st.session_state:
        st.divider()
        if st.button("Clear results", use_container_width=True):
            for key in ("results", "report", "report_obj", "mitre_techniques",
                        "last_query", "model_name", "iocs", "timeline", "analyst_notes"):
                st.session_state.pop(key, None)
            st.rerun()


# --- Case Header ---
st.header("Incident Investigation")

col_title, col_sev = st.columns([3, 1])
with col_title:
    case_title = st.text_input(
        "Case title",
        placeholder="e.g. CASE-2026-042 — Ransomware on PROD-DB-01",
        key="case_title",
    )
with col_sev:
    severity = st.selectbox(
        "Severity",
        options=["Critical", "High", "Medium", "Low"],
        index=1,
        key="severity",
    )

if severity:
    st.markdown(_severity_badge(severity), unsafe_allow_html=True)
    st.write("")

# --- Query input ---
query = st.text_area(
    "Describe the incident or paste IOCs / log snippets:",
    height=130,
    placeholder=(
        "e.g. Suspicious PowerShell execution at 14:32, lateral movement "
        "detected to 10.0.0.5, new scheduled task created..."
    ),
    key="query_input",
)

col_btn, col_hint = st.columns([1, 4])
with col_btn:
    investigate = st.button("Investigate", type="primary", disabled=(kb_size == 0))
with col_hint:
    if kb_size == 0:
        st.caption("Run `python ingest.py` to populate the knowledge base first.")


# --- Investigate action ---
if investigate:
    if not query.strip():
        st.warning("Please enter an incident description before investigating.")
    else:
        with st.spinner("Searching knowledge base..."):
            try:
                results = retrieve(query, top_k=top_k)
                st.session_state["results"] = results
                st.session_state["last_query"] = query
                st.session_state["model_name"] = model_name

                # IOC extraction over query + all retrieved chunk texts
                combined_text = query + " " + " ".join(c["text"] for c in results)
                st.session_state["iocs"] = extract_iocs(combined_text)

                # Auto-extract timestamps from query for timeline seed
                ts_pattern = re.compile(
                    r"\b(?:\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?Z?|"
                    r"\d{1,2}:\d{2}(?::\d{2})?)\b"
                )
                existing_times = {e["time"] for e in st.session_state.get("timeline", [])}
                auto_entries = [
                    {"time": m.group(), "event": ""}
                    for m in ts_pattern.finditer(query)
                    if m.group() not in existing_times
                ]
                # Merge auto-extracted entries with any existing manual ones
                st.session_state["timeline"] = (
                    st.session_state.get("timeline", []) + auto_entries
                )

                # Clear stale report from a previous investigation
                for key in ("report", "report_obj", "mitre_techniques"):
                    st.session_state.pop(key, None)

            except Exception as e:
                st.error(f"Retrieval error: {e}")
                st.session_state.pop("results", None)


# --- Tabbed results ---
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    last_query = st.session_state.get("last_query", "")
    saved_model = st.session_state.get("model_name", model_name)

    st.divider()

    tab_evidence, tab_timeline, tab_iocs, tab_mitre, tab_report = st.tabs([
        "📋 Evidence",
        "🕐 Timeline",
        "🔎 IOCs",
        "🛡 MITRE ATT&CK",
        "📄 Report",
    ])

    # ── Tab 1: Evidence ─────────────────────────────────────────────────────
    with tab_evidence:
        st.subheader("Retrieved Evidence")
        st.caption(f"Query: *{last_query[:100]}{'...' if len(last_query) > 100 else ''}*")

        import pandas as pd
        rows = []
        for i, chunk in enumerate(results, 1):
            dist = chunk["distance"]
            if dist < 1.0:
                rel = "🟢 High"
            elif dist < 1.3:
                rel = "🟡 Medium"
            else:
                rel = "🔴 Low"
            rows.append({
                "#": i,
                "Source": chunk["source"],
                "Preview": chunk["text"][:120].replace("\n", " ") + "…",
                "Distance": round(dist, 4),
                "Relevance": rel,
            })
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "#": st.column_config.NumberColumn(width="small"),
                "Distance": st.column_config.NumberColumn(format="%.4f", width="small"),
            },
        )

        st.divider()
        st.caption("Full chunk text")
        for i, chunk in enumerate(results, 1):
            dist = chunk["distance"]
            badge = "🟢 High" if dist < 1.0 else ("🟡 Medium" if dist < 1.3 else "🔴 Low")
            with st.expander(f"[{i}] {badge} relevance  |  📄 {chunk['source']}"):
                st.markdown(chunk["text"])

    # ── Tab 2: Timeline ──────────────────────────────────────────────────────
    with tab_timeline:
        st.subheader("Incident Timeline")
        st.caption("Auto-extracted from your query. Add, edit, or remove entries below.")

        timeline: list[dict] = st.session_state.get("timeline", [])

        to_delete = []
        for idx, entry in enumerate(timeline):
            col_time, col_event, col_del = st.columns([2, 6, 1])
            with col_time:
                new_time = st.text_input(
                    "Time", value=entry.get("time", ""),
                    key=f"tl_time_{idx}", label_visibility="collapsed",
                    placeholder="HH:MM",
                )
                timeline[idx]["time"] = new_time
            with col_event:
                new_event = st.text_input(
                    "Event", value=entry.get("event", ""),
                    key=f"tl_event_{idx}", label_visibility="collapsed",
                    placeholder="Describe the event…",
                )
                timeline[idx]["event"] = new_event
            with col_del:
                if st.button("🗑", key=f"tl_del_{idx}", help="Remove this entry"):
                    to_delete.append(idx)

        for idx in reversed(to_delete):
            timeline.pop(idx)

        st.session_state["timeline"] = timeline

        if st.button("+ Add event"):
            st.session_state["timeline"].append({"time": "", "event": ""})
            st.rerun()

    # ── Tab 3: IOCs ──────────────────────────────────────────────────────────
    with tab_iocs:
        st.subheader("IOC Summary")
        iocs: dict = st.session_state.get("iocs", {})

        total = sum(len(v) for v in iocs.values())
        if total == 0:
            st.info("No IOCs detected in the query or retrieved context.")
        else:
            st.caption(f"{total} indicator(s) extracted from query and retrieved chunks.")

        # Display in rows of 3 columns
        categories = [k for k, v in iocs.items() if v]
        empties = [k for k, v in iocs.items() if not v]

        for i in range(0, len(categories), 3):
            cols = st.columns(3)
            for col, cat in zip(cols, categories[i:i + 3]):
                with col:
                    items = iocs[cat]
                    st.metric(cat, len(items))
                    st.code("\n".join(items), language=None)

        if empties:
            with st.expander("Categories with no findings"):
                st.write(", ".join(empties))

    # ── Tab 4: MITRE ATT&CK ─────────────────────────────────────────────────
    with tab_mitre:
        st.subheader("MITRE ATT&CK Techniques")

        if "mitre_techniques" not in st.session_state:
            st.info("Generate a report to populate MITRE technique mappings.")
        elif not st.session_state["mitre_techniques"]:
            st.info("No MITRE ATT&CK techniques identified in the report or context.")
        else:
            techniques = st.session_state["mitre_techniques"]
            st.caption(f"{len(techniques)} technique(s) detected across retrieved context and report")

            by_tactic: dict[str, list] = {}
            for t in techniques:
                by_tactic.setdefault(t["tactic"], []).append(t)

            for tactic, techs in by_tactic.items():
                st.markdown(f"**{tactic}**")
                cols = st.columns(min(len(techs), 3))
                for col, tech in zip(cols, techs):
                    with col:
                        st.markdown(
                            f"[{tech['id']}]({tech['url']})  \n"
                            f"*{tech['name']}*"
                        )
                if len(techs) > 3:
                    for tech in techs[3:]:
                        st.markdown(f"- [{tech['id']}]({tech['url']}) — *{tech['name']}*")

    # ── Tab 5: Report ────────────────────────────────────────────────────────
    with tab_report:
        st.subheader("Investigation Report")

        if st.button("Generate Report", type="secondary"):
            try:
                _raw = st.write_stream(
                    generate_report(last_query, results, model=saved_model)
                )
                full_report_text = _raw if isinstance(_raw, str) else ""
                st.session_state["report"] = full_report_text

                context_text = " ".join(c["text"] for c in results)
                techniques = techniques_from_texts(context_text, full_report_text)
                st.session_state["mitre_techniques"] = techniques

                # Build structured report object for export
                report_obj = build_report(
                    llm_text=full_report_text,
                    case_title=st.session_state.get("case_title", ""),
                    severity=st.session_state.get("severity", "High"),
                    query=last_query,
                    timeline=st.session_state.get("timeline", []),
                    analyst_notes=st.session_state.get("analyst_notes", ""),
                    evidence_chunks=results,
                    mitre_techniques=techniques,
                )
                st.session_state["report_obj"] = report_obj

            except ConnectionError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"LLM error: {e}")

        elif "report" in st.session_state:
            st.markdown(st.session_state["report"])

        # Analyst notes — persists across reruns
        analyst_notes = st.text_area(
            "Analyst Notes",
            value=st.session_state.get("analyst_notes", ""),
            height=100,
            placeholder="Add your observations, hypotheses, or next actions here…",
            key="analyst_notes",
        )

        # Export buttons — only when report exists
        if "report_obj" in st.session_state:
            report_obj = st.session_state["report_obj"]

            # Refresh analyst notes into report_obj before export
            report_obj.analyst_notes = analyst_notes
            report_obj.timeline = st.session_state.get("timeline", [])

            st.divider()
            st.caption("Export investigation report")
            col_md, col_pdf = st.columns(2)

            with col_md:
                st.download_button(
                    label="⬇ Download Markdown",
                    data=to_markdown(report_obj),
                    file_name=md_filename(report_obj),
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_pdf:
                st.download_button(
                    label="⬇ Download PDF",
                    data=to_pdf(report_obj),
                    file_name=pdf_filename(report_obj),
                    mime="application/pdf",
                    use_container_width=True,
                )


# --- Footer ---
st.divider()
st.caption("AttackGraph AI — powered by ChromaDB · SentenceTransformers · Ollama · Streamlit")
