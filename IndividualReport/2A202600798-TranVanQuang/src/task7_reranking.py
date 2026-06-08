"""Task 7 - Reranking.

The default reranker is a local cross-encoder-style proxy: it combines the
incoming retrieval score with token overlap between query and candidate. RRF is
also implemented for hybrid fusion.
"""

from .local_rag_utils import keyword_overlap_score


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Re-score candidates using keyword overlap plus original retrieval score."""
    reranked = []
    for candidate in candidates:
        overlap = keyword_overlap_score(query, candidate.get("content", ""))
        original = float(candidate.get("score", 0.0))
        score = 0.65 * overlap + 0.35 * original
        item = candidate.copy()
        item["score"] = float(score)
        item.setdefault("metadata", {})
        reranked.append(item)
    reranked.sort(key=lambda item: item["score"], reverse=True)
    return reranked[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """Select diverse high-scoring candidates using their existing scores."""
    del query_embedding
    selected = []
    seen_sources = set()
    for candidate in sorted(candidates, key=lambda item: item.get("score", 0), reverse=True):
        source = candidate.get("metadata", {}).get("source")
        diversity_bonus = 0.05 if source not in seen_sources else 0.0
        item = candidate.copy()
        item["score"] = float(lambda_param * item.get("score", 0.0) + diversity_bonus)
        selected.append(item)
        seen_sources.add(source)
        if len(selected) >= top_k:
            break
    selected.sort(key=lambda item: item["score"], reverse=True)
    return selected


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """Reciprocal Rank Fusion for combining multiple ranked result lists."""
    scores = {}
    items = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            metadata = item.get("metadata", {})
            key = (
                metadata.get("path"),
                metadata.get("chunk_index"),
                item.get("content", "")[:80],
            )
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in items or item.get("score", 0) > items[key].get("score", 0):
                items[key] = item

    fused = []
    for key, score in scores.items():
        item = items[key].copy()
        item["score"] = float(score)
        fused.append(item)
    fused.sort(key=lambda item: item["score"], reverse=True)
    return fused[:top_k]


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",
) -> list[dict]:
    """Unified reranking interface."""
    if not candidates or top_k <= 0:
        return []
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    if method == "mmr":
        return rerank_mmr([], candidates, top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k)
    raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy = [
        {"content": "Tội tàng trữ ma túy", "score": 0.8, "metadata": {}},
        {"content": "Python programming", "score": 0.7, "metadata": {}},
    ]
    print(rerank("hình phạt ma túy", dummy, top_k=2))
