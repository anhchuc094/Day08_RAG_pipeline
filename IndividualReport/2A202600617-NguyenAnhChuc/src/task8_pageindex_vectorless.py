"""Task 8 - PageIndex-style vectorless fallback."""

from .local_rag_utils import overlap
from .task4_chunking_indexing import load_or_build_index


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    if top_k <= 0:
        return []
    results = []
    for item in load_or_build_index():
        results.append(
            {
                "content": item["content"],
                "score": float(overlap(query, item["content"])),
                "metadata": item.get("metadata", {}),
                "source": "pageindex",
            }
        )
    results.sort(key=lambda row: row["score"], reverse=True)
    return results[:top_k]
