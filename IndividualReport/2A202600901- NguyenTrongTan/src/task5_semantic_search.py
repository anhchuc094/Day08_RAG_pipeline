"""
Task 5 — Semantic Search Module.
"""

from .store_utils import query_chromadb


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    return query_chromadb(query, top_k)


if __name__ == "__main__":
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
