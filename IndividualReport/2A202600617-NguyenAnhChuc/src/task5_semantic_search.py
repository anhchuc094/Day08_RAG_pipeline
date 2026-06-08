"""Task 5 - Semantic search."""

from .local_rag_utils import dot, stable_embedding
from .task4_chunking_indexing import EMBEDDING_DIM, load_or_build_index


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    if top_k <= 0:
        return []
    query_vector = stable_embedding(query, EMBEDDING_DIM)
    results = []
    for item in load_or_build_index():
        score = dot(query_vector, item.get("embedding", []))
        results.append(
            {
                "content": item["content"],
                "score": float(score),
                "metadata": item.get("metadata", {}),
            }
        )
    results.sort(key=lambda row: row["score"], reverse=True)
    return results[:top_k]
