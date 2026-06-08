"""Task 5 - Semantic search over the local vector index."""

from .local_rag_utils import cosine_similarity, hashed_embedding
from .task4_chunking_indexing import EMBEDDING_DIM, load_or_build_index


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Return top_k chunks ranked by cosine similarity."""
    if top_k <= 0:
        return []

    query_embedding = hashed_embedding(query, EMBEDDING_DIM)
    results = []
    for chunk in load_or_build_index():
        score = cosine_similarity(query_embedding, chunk.get("embedding", []))
        results.append(
            {
                "content": chunk["content"],
                "score": float(score),
                "metadata": chunk.get("metadata", {}),
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("hinh phat ma tuy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
