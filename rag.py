"""
rag.py — Given a query, finds the most relevant chunks from ChromaDB.
"""

import os


# Same path as ingest.py — Linux filesystem for fast SQLite I/O under WSL2
CHROMA_DIR = os.path.expanduser("~/.attackgraph_chroma")
COLLECTION_NAME = "threat_docs"
EMBED_MODEL = "all-MiniLM-L6-v2"

# Module-level cache so the model and DB connection are only loaded once per process
_model = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        import chromadb
        if not os.path.exists(CHROMA_DIR):
            raise FileNotFoundError(
                f"ChromaDB not found at '{CHROMA_DIR}'. Run `python ingest.py` first."
            )
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection

def ingest_chunks(
    texts: list[str],
    source: str,
    file_type: str,
    doc_id: str,
) -> int:
    """
    Embed and upsert a list of text chunks into the ChromaDB collection.
    Reuses the module-level cached model and collection so a second copy of
    the embedding model is never loaded during an active Streamlit session.
    Returns the number of chunks stored.
    """
    if not texts:
        return 0

    # Ensure the DB directory exists before trying to open it
    os.makedirs(CHROMA_DIR, exist_ok=True)

    model = _get_model()
    collection = _get_collection()
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    ids = [f"{doc_id}_chunk{i}" for i in range(len(texts))]
    metadatas = [
        {"source": source, "file_type": file_type, "chunk_index": i}
        for i in range(len(texts))
    ]
    collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    return len(texts)


def collection_size() -> int:
    """Return how many chunks are stored, or 0 if the DB doesn't exist yet."""
    sqlite_path = os.path.join(CHROMA_DIR, "chroma.sqlite3")
    if not os.path.exists(sqlite_path):
        return 0
    return _get_collection().count()


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Embed the query and return the top_k most similar document chunks.
    Each result is a dict with 'text', 'source', and 'distance'.
    Raises FileNotFoundError if ingest hasn't been run yet.
    """
    collection = _get_collection()

    # Guard: can't query more results than are stored
    count = collection.count()
    if count == 0:
        raise ValueError("The knowledge base is empty. Run `python ingest.py` first.")
    top_k = min(top_k, count)

    model = _get_model()
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Flatten ChromaDB's nested response into a simple list
    chunks = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": text,
            "source": meta.get("source", "unknown"),
            "distance": dist,
        })

    return chunks
