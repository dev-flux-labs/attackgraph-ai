"""
ingest.py — loads documents from data/, embeds them, and stores in ChromaDB.
Run this once (or whenever you add new documents) before starting the app.

Usage:
    python ingest.py           # ingest new/updated docs
    python ingest.py --reset   # wipe the collection and re-ingest everything
"""

import os
import sys
import chromadb
from sentence_transformers import SentenceTransformer

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
# Store ChromaDB on the Linux filesystem — avoids the slow SQLite I/O
# that occurs when the path crosses the WSL2/Windows boundary (/mnt/e/).
CHROMA_DIR = os.path.expanduser("~/.attackgraph_chroma")
COLLECTION_NAME = "threat_docs"
EMBED_MODEL = "all-MiniLM-L6-v2"  # fast, runs locally, no GPU needed


def load_documents(data_dir: str) -> list[dict]:
    """Read all .txt files from data_dir. Returns list of {id, text, source}."""
    docs = []
    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".txt"):
            continue
        path = os.path.join(data_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
        except (OSError, UnicodeDecodeError) as e:
            print(f"  WARNING: skipping {filename} — {e}")
            continue
        if text:
            docs.append({"id": filename, "text": text, "source": filename})
    return docs


def chunk_text(text: str, max_chars: int = 600, overlap_chars: int = 80) -> list[str]:
    """
    Split text into chunks by paragraph first, then by size.
    Paragraph-aware chunking keeps related sentences together, which
    improves retrieval quality compared to blind character splits.
    """
    # Split on blank lines to get natural paragraph boundaries
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph would exceed the limit, flush current chunk
        if current_chunk and len(current_chunk) + len(para) + 2 > max_chars:
            chunks.append(current_chunk.strip())
            # Carry the tail of the previous chunk into the next for context overlap
            overlap = current_chunk[-overlap_chars:] if len(current_chunk) > overlap_chars else current_chunk
            current_chunk = overlap + "\n\n" + para
        else:
            current_chunk = (current_chunk + "\n\n" + para).strip() if current_chunk else para

        # A single paragraph longer than max_chars gets split by sentence
        if len(current_chunk) > max_chars * 1.5:
            sentences = current_chunk.replace(". ", ".\n").split("\n")
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) > max_chars:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk = (current_chunk + " " + sentence).strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def ingest(reset: bool = False):
    """Main ingestion function — load, chunk, embed, store."""
    print(f"Loading documents from '{DATA_DIR}'...")
    docs = load_documents(DATA_DIR)
    if not docs:
        print("No .txt files found in data/. Add some documents and re-run.")
        return

    print(f"Found {len(docs)} document(s).")

    print(f"Loading embedding model '{EMBED_MODEL}'...")
    model = SentenceTransformer(EMBED_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    if reset:
        # Delete the collection so we start fresh — useful after editing source docs
        existing = [c.name for c in client.list_collections()]
        if COLLECTION_NAME in existing:
            client.delete_collection(COLLECTION_NAME)
            print("Existing collection wiped.")

    collection = client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    all_ids, all_texts, all_metas = [], [], []

    for doc in docs:
        chunks = chunk_text(doc["text"])
        print(f"  {doc['source']}: {len(chunks)} chunk(s)")
        for i, chunk in enumerate(chunks):
            all_ids.append(f"{doc['id']}_chunk{i}")
            all_texts.append(chunk)
            all_metas.append({"source": doc["source"], "chunk_index": i})

    print(f"\nEmbedding {len(all_texts)} chunk(s)...")
    embeddings = model.encode(all_texts, show_progress_bar=True).tolist()

    # Upsert so re-running without --reset doesn't duplicate chunks
    collection.upsert(
        ids=all_ids,
        documents=all_texts,
        embeddings=embeddings,
        metadatas=all_metas,
    )

    print(f"\nDone. {len(all_texts)} chunk(s) stored in '{CHROMA_DIR}'.")
    print(f"Collection '{COLLECTION_NAME}' now has {collection.count()} total chunk(s).")


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    ingest(reset=reset_flag)
