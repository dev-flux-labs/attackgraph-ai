"""
app.py — Streamlit UI entry point.
Run with: streamlit run app.py
"""

import streamlit as st
from rag import retrieve, collection_size
from llm import generate_report
from mitre import techniques_from_texts

st.set_page_config(
    page_title="AttackGraph AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.title("🔍 AttackGraph AI")
    st.caption("Cybersecurity incident investigation assistant")
    st.divider()

    kb_size = collection_size()
    if kb_size == 0:
        st.error("Knowledge base empty — run `python ingest.py` first.")
    else:
        st.metric("Knowledge Base", f"{kb_size} chunks", help="Threat intel chunks indexed in ChromaDB")

    st.divider()
    st.subheader("Settings")
    top_k = st.slider("Results to retrieve", min_value=1, max_value=10, value=5)
    model_name = st.text_input(
        "Ollama model", value="llama3.2",
        help="Run `ollama pull <model>` to download a model."
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
            # Clear previous results when a new example is selected
            st.session_state.pop("results", None)
            st.session_state.pop("report", None)
            st.session_state.pop("mitre_techniques", None)

    # Clear button at the bottom of the sidebar
    if "results" in st.session_state:
        st.divider()
        if st.button("Clear results", use_container_width=True):
            for key in ["results", "report", "mitre_techniques", "last_query", "model_name"]:
                st.session_state.pop(key, None)
            st.rerun()

# --- Main area ---
st.header("Incident Investigation")

query = st.text_area(
    "Describe the incident or paste IOCs / log snippets:",
    height=140,
    placeholder="e.g. Suspicious PowerShell execution, lateral movement detected to 10.0.0.5, new scheduled task created...",
    key="query_input",
)

col_btn, col_hint = st.columns([1, 4])
with col_btn:
    investigate = st.button("Investigate", type="primary", disabled=(kb_size == 0))
with col_hint:
    if kb_size == 0:
        st.caption("Run `python ingest.py` to populate the knowledge base first.")

if investigate:
    if not query.strip():
        st.warning("Please enter an incident description before investigating.")
    else:
        with st.spinner("Searching knowledge base..."):
            try:
                st.session_state["results"] = retrieve(query, top_k=top_k)
                st.session_state["last_query"] = query
                st.session_state["model_name"] = model_name
                st.session_state.pop("report", None)
                st.session_state.pop("mitre_techniques", None)
            except Exception as e:
                st.error(f"Retrieval error: {e}")
                st.session_state.pop("results", None)

# --- Results ---
if "results" in st.session_state and st.session_state["results"]:
    results = st.session_state["results"]
    last_query = st.session_state.get("last_query", "")
    saved_model = st.session_state.get("model_name", model_name)

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Relevant Context")
    with col2:
        st.caption(f"Query: *{last_query[:80]}{'...' if len(last_query) > 80 else ''}*")

    for i, chunk in enumerate(results, 1):
        dist = chunk["distance"]
        if dist < 1.0:
            badge = "🟢 High"
        elif dist < 1.3:
            badge = "🟡 Medium"
        else:
            badge = "🔴 Low"

        label = f"{badge} relevance  |  📄 {chunk['source']}"
        with st.expander(f"[{i}] {label}", expanded=(i == 1)):
            st.markdown(chunk["text"])

    # --- LLM report ---
    st.divider()
    st.subheader("Investigation Report")

    if st.button("Generate Report", type="secondary"):
        try:
            _raw = st.write_stream(
                generate_report(last_query, results, model=saved_model)
            )
            full_report = _raw if isinstance(_raw, str) else ""
            st.session_state["report"] = full_report

            context_text = " ".join(c["text"] for c in results)
            techniques = techniques_from_texts(context_text, full_report)
            st.session_state["mitre_techniques"] = techniques

        except ConnectionError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"LLM error: {e}")

    elif "report" in st.session_state:
        st.markdown(st.session_state["report"])

    # --- MITRE ATT&CK ---
    if "mitre_techniques" in st.session_state and st.session_state["mitre_techniques"]:
        techniques = st.session_state["mitre_techniques"]

        st.divider()
        st.subheader("MITRE ATT&CK Techniques Identified")
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

# --- Footer ---
st.divider()
st.caption("AttackGraph AI — powered by ChromaDB · SentenceTransformers · Ollama · Streamlit")
