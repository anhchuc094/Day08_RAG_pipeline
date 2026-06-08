"""
Task 7 — Reranking Module.
"""

import re
from typing import Optional

from .store_utils import embed_texts, tokenize


def _keyword_overlap_score(query: str, content: str) -> float:
    q_tokens = set(tokenize(query))
    c_tokens = set(tokenize(content))
    if not q_tokens:
        return 0.0
    return len(q_tokens & c_tokens) / len(q_tokens)


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    scored = []
    for c in candidates:
        overlap = _keyword_overlap_score(query, c["content"])
        base = float(c.get("score", 0.0))
        combined = 0.6 * min(base, 1.0) + 0.4 * overlap
        item = c.copy()
        item["score"] = combined
        scored.append(item)

    scored.sort(key=lambda x: x["score"], reverse=True)
    results = scored[:top_k]
    if results:
        max_s = max(r["score"] for r in results)
        min_s = min(r["score"] for r in results)
        span = max_s - min_s
        for r in results:
            if span > 0:
                r["score"] = (r["score"] - min_s) / span
            else:
                r["score"] = 1.0
    return results


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    if not candidates:
        return []

    embeddings = []
    for c in candidates:
        if "embedding" in c:
            embeddings.append(c["embedding"])
        else:
            embeddings.append(embed_texts([c["content"]])[0])

    selected: list[int] = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float("-inf")

        for idx in remaining:
            relevance = _cosine_sim(query_embedding, embeddings[idx])
            max_sim_to_selected = 0.0
            for sel_idx in selected:
                sim = _cosine_sim(embeddings[idx], embeddings[sel_idx])
                max_sim_to_selected = max(max_sim_to_selected, sim)
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        selected.append(best_idx)
        remaining.remove(best_idx)

    results = []
    for idx in selected:
        item = candidates[idx].copy()
        item["score"] = float(item.get("score", 0.0))
        results.append(item)
    return results


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    rrf_scores: dict[str, float] = {}
    content_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            content_map[key] = item

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = score
        results.append(item)
    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",
) -> list[dict]:
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        query_embedding = embed_texts([query])[0]
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf":
        return rerank_rrf([candidates], top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
