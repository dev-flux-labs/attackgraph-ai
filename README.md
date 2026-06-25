# AttackGraph AI

A local, privacy-preserving cybersecurity incident investigation assistant built with RAG (Retrieval-Augmented Generation). Paste an incident description or IOCs, and the tool retrieves relevant threat intelligence, generates a structured investigation report, and maps the activity to MITRE ATT&CK techniques — all running on your machine.

---

## Features

- **RAG pipeline** — queries are embedded and matched against a local ChromaDB vector store of threat intelligence documents
- **Streaming LLM report** — Ollama generates a structured report (Incident Summary, IOCs, Attack Techniques, Next Steps) streamed token-by-token
- **MITRE ATT&CK mapping** — automatically extracts and enriches T-IDs from retrieved context and the LLM report, grouped by tactic
- **Fully local** — no data leaves your machine (SentenceTransformers + Ollama, no API keys)

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running

---

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd attackgraph-ai

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull an Ollama model (one-time download, ~2 GB)
ollama pull llama3.2
```

---

## Usage

### Step 1 — Ingest documents

Place `.txt` threat intelligence documents in the `data/` folder, then run:

```bash
python ingest.py
```

Three sample documents are included (lateral movement, ransomware TTPs, phishing campaigns). To re-ingest after editing documents:

```bash
python ingest.py --reset
```

### Step 2 — Start Ollama

```bash
ollama serve
```

### Step 3 — Launch the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Demo Flow

1. The sidebar shows the knowledge base status and a `top_k` slider
2. Click an example query or type your own incident description
3. Click **Investigate** — the top matching chunks appear with relevance badges (🟢 High / 🟡 Medium / 🔴 Low)
4. Click **Generate Report** — the LLM streams a structured investigation report
5. MITRE ATT&CK techniques are extracted automatically and displayed as linked cards grouped by tactic

---

## Architecture

```
data/                      # Source .txt threat intelligence documents
ingest.py                  # Chunks, embeds, and stores documents in ChromaDB
~/.attackgraph_chroma/     # Persisted vector store (outside repo, auto-created)
rag.py                     # Embeds queries and retrieves top-k chunks
llm.py                     # Builds prompts and streams Ollama responses
mitre.py                   # Extracts and enriches MITRE ATT&CK technique IDs
app.py                     # Streamlit UI
test_retrieval.py          # Manual retrieval quality check
```

**Ingestion pipeline** (`ingest.py`):
Documents → paragraph-aware chunking → `all-MiniLM-L6-v2` embeddings → ChromaDB upsert (cosine similarity)

**Retrieval pipeline** (`rag.py`):
Query → embed → ChromaDB cosine similarity search → top-k chunks

**Generation pipeline** (`llm.py` + `app.py`):
Query + chunks → structured prompt → Ollama (`llama3.2`) → streamed markdown report

**MITRE mapping** (`mitre.py`):
Retrieved text + LLM report → regex T-ID extraction → technique lookup → tactic-grouped cards

---

## Adding Your Own Documents

Drop any `.txt` file into `data/` and re-run `python ingest.py --reset`. The tool works best with structured threat reports, TTP descriptions, runbooks, or SIEM alert documentation.

---

## Tech Stack

| Component | Library |
|---|---|
| UI | Streamlit |
| Vector store | ChromaDB |
| Embeddings | SentenceTransformers (`all-MiniLM-L6-v2`) |
| LLM | Ollama (default: `llama3.2`) |
| ATT&CK mapping | Custom regex + lookup dict |
