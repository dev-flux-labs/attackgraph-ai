# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Build a Streamlit cybersecurity incident investigation assistant using RAG (Retrieval-Augmented Generation). Capstone project — prioritize a working MVP over polish.

## Tech Stack

- Python 3.12 (venv at `./venv/`)
- Streamlit — UI
- ChromaDB — vector store
- SentenceTransformers — local embeddings
- Ollama — local LLM (added in phase 5)

## Development Commands

```bash
# Activate venv (always do this first)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py

# Ingest documents into ChromaDB
python ingest.py

# Run with a specific port
streamlit run app.py --server.port 8501
```

## Planned Architecture

The app has two main pipelines:

**Ingestion pipeline** (`ingest.py`):
- Loads raw documents (threat reports, logs, CVE data) from `data/`
- Chunks and embeds them with SentenceTransformers
- Stores vectors + metadata in ChromaDB (`chroma_db/`)

**Retrieval + generation pipeline** (`app.py` or `rag.py`):
- User submits a natural-language query in Streamlit
- Query is embedded → ChromaDB similarity search → top-k chunks retrieved
- Retrieved chunks are passed as context to Ollama (local LLM)
- LLM generates an investigation report, optionally with MITRE ATT&CK mapping

**Expected file layout** (not yet created):
```
data/           # raw source documents
chroma_db/      # persisted ChromaDB vector store
ingest.py       # ingestion pipeline
rag.py          # retrieval logic
app.py          # Streamlit UI entry point
requirements.txt
```

## Development Phases

1. Project skeleton
2. Ingestion pipeline
3. Retrieval pipeline
4. Streamlit UI
5. LLM investigation report (Ollama)
6. MITRE ATT&CK mapping
7. README and demo polish

## Rules

- Keep it simple — no LangChain, no Neo4j, no multi-agent system.
- Code must be beginner-readable with comments.
- Explain before major architecture changes.
- When asked to code: give a short plan, list files to modify, then implement.
