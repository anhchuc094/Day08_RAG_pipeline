"""Task 9 - Hybrid retrieval pipeline."""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

DEFAULT_TOP_K = 5
SCORE_THRESHOLD = 0.3


def retrieve(query: str, top_k: int = DEFAULT_TOP_K, score_threshold: float = SCORE_THRESHOLD) -> list[dict]:
    if top_k <= 0:
        return []
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)
    fused = rerank_rrf([dense, sparse], top_k=top_k * 2)
    for item in fused:
        item["source"] = "hybrid"

    final = rerank(query, fused, top_k=top_k)
    for item in final:
        item["source"] = "hybrid"

    if not final or final[0].get("score", 0.0) < score_threshold:
        return pageindex_search(query, top_k=top_k)
    return final[:top_k]
