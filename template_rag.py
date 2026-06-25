"""
template_rag.py — SOC report template retrieval layer.

Templates in report_templates/ are stored in a separate ChromaDB collection
('report_templates') so they never appear in the threat-intel Evidence tab.

Public API:
    ensure_templates_ingested()  — idempotent; call once at app startup
    get_relevant_template(query) — returns (name, text) or None
"""

import os
import re
from pathlib import Path

# Reuse the same ChromaDB location and embedding model as rag.py
from rag import CHROMA_DIR, EMBED_MODEL, _get_model

TEMPLATE_DIR = Path(__file__).parent / "report_templates"
COLLECTION_NAME = "report_templates"

# If the best-matching template is further than this cosine distance, skip it.
# 0.8 is permissive enough to catch clear matches while avoiding forcing an
# unrelated template onto a vague query.
TEMPLATE_THRESHOLD = 0.70

_template_collection = None


def _get_template_collection():
    global _template_collection
    if _template_collection is None:
        import chromadb
        os.makedirs(CHROMA_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _template_collection = client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _template_collection


def ensure_templates_ingested() -> None:
    """
    Load all .txt files from report_templates/ into the ChromaDB collection.
    Only runs the embedding step when the collection is empty, so it is
    safe to call on every app startup.
    """
    collection = _get_template_collection()
    if collection.count() > 0:
        return  # already loaded

    template_files = sorted(TEMPLATE_DIR.glob("*.txt"))
    if not template_files:
        print("WARNING: report_templates/ is empty — no templates to ingest.")
        return

    model = _get_model()

    ids, texts, metas = [], [], []
    for path in template_files:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        ids.append(path.stem)                             # e.g. "ransomware_investigation"
        texts.append(text)
        metas.append({"filename": path.name, "stem": path.stem})

    embeddings = model.encode(texts, show_progress_bar=False).tolist()
    collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metas)
    print(f"Template RAG: {len(ids)} template(s) ingested into '{COLLECTION_NAME}'.")


def _extract_template_name(text: str) -> str:
    """
    Pull the display name from the first line of a template.
    '[Template: Ransomware Investigation Report]' → 'Ransomware Investigation Report'
    Falls back to the raw first line if the pattern doesn't match.
    """
    first_line = text.splitlines()[0].strip() if text else ""
    match = re.match(r"\[Template:\s*(.+?)\]", first_line)
    return match.group(1).strip() if match else first_line


def get_relevant_template(query: str) -> tuple[str, str] | None:
    """
    Embed the query and retrieve the most semantically similar report template.

    Returns (template_display_name, template_text) if the best match is within
    TEMPLATE_THRESHOLD cosine distance, otherwise None (caller uses generic prompt).
    """
    collection = _get_template_collection()
    if collection.count() == 0:
        return None

    model = _get_model()
    embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[embedding],
        n_results=1,
        include=["documents", "distances"],
    )

    distance = results["distances"][0][0]
    if distance >= TEMPLATE_THRESHOLD:
        return None

    text = results["documents"][0][0]
    name = _extract_template_name(text)
    return name, text
