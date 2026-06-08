"""Task 7 - Reranking and rank fusion."""

from .local_rag_utils import overlap


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    scores = {}
    best_items = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked, start=1):
            meta = item.get("metadata", {})
            key = (meta.get("path"), meta.get("chunk_index"), item.get("content", "")[:96])
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in best_items or item.get("score", 0.0) > best_items[key].get("score", 0.0):
                best_items[key] = item

    fused = []
    for key, score in scores.items():
        row = best_items[key].copy()
        row["score"] = float(score)
        fused.append(row)
    fused.sort(key=lambda row: row["score"], reverse=True)
    return fused[:top_k]


def rerank(query: str, candidates: list[dict], top_k: int = 5, method: str = "local") -> list[dict]:
    del method
    if top_k <= 0:
        return []
    rescored = []
    for rank, item in enumerate(candidates, start=1):
        local_score = overlap(query, item.get("content", ""))
        rank_bonus = 1.0 / (rank + 10)
        score = 0.7 * local_score + 0.2 * float(item.get("score", 0.0)) + 0.1 * rank_bonus
        row = item.copy()
        row["score"] = float(score)
        row.setdefault("metadata", {})
        rescored.append(row)
    rescored.sort(key=lambda row: row["score"], reverse=True)
    return rescored[:top_k]
