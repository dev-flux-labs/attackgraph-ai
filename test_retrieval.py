"""
test_retrieval.py — manually test retrieval quality before wiring up the UI.
Run with: python test_retrieval.py
"""

from rag import retrieve, collection_size

# A set of queries that should map to different documents
TEST_QUERIES = [
    "suspicious PowerShell execution and lateral movement",
    "ransomware deleting shadow copies and encrypting files",
    "phishing email with malicious attachment bypassing MFA",
    "Mimikatz pass the hash NTLM authentication",
    "Cobalt Strike beacon C2 traffic",
]


def main():
    size = collection_size()
    if size == 0:
        print("Knowledge base is empty. Run `python ingest.py` first.")
        return

    print(f"Knowledge base: {size} chunks\n")
    print("=" * 70)

    for query in TEST_QUERIES:
        print(f"\nQUERY: {query}")
        print("-" * 70)

        results = retrieve(query, top_k=3)
        for i, chunk in enumerate(results, 1):
            # Print source and relevance score, then a short preview of the text
            preview = chunk["text"][:200].replace("\n", " ")
            print(f"  [{i}] {chunk['source']}  (distance: {chunk['distance']:.4f})")
            print(f"      {preview}...")

        print()


if __name__ == "__main__":
    main()
