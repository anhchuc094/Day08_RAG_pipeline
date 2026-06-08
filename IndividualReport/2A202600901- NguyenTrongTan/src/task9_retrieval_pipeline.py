"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search

SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"


def _normalize_scores(results: list[dict]) -> list[dict]:
    if not results:
        return results
    scores = [r["score"] for r in results]
    max_s = max(scores)
    min_s = min(scores)
    span = max_s - min_s
    normalized = []
    for r in results:
        item = r.copy()
        if span > 0:
            item["score"] = (r["score"] - min_s) / span
        else:
            item["score"] = 1.0
        normalized.append(item)
    return normalized


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    dense_results = semantic_search(query, top_k=top_k * 2)
    sparse_results = lexical_search(query, top_k=top_k * 2)

    if not dense_results and not sparse_results:
        return pageindex_search(query, top_k=top_k)

    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)
    for item in merged:
        item["source"] = "hybrid"

    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        for item in final_results:
            item["source"] = "hybrid"
    else:
        final_results = merged[:top_k]

    final_results = _normalize_scores(final_results)

    if not final_results or final_results[0]["score"] < score_threshold:
        fallback = pageindex_search(query, top_k=top_k)
        return fallback

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Nghệ sĩ nào bị bắt vì sử dụng ma tuý năm 2024",
        "Luật phòng chống ma tuý 2021 quy định gì về cai nghiện",
    ]
    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {r['content'][:80]}...")
