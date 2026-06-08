"""Lightweight retrieval pipeline for the group project."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

from group_project.rag.documents import load_chunks

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")

STOPWORDS = {
    "la", "gi", "co", "the", "nhu", "nao", "ve", "va", "hoac", "theo",
    "trong", "ngoai", "duoc", "bi", "cac", "nhung", "mot", "nguoi", "chat",
}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Ä‘", "d")


def tokenize(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(normalize_text(text))
    return [token for token in tokens if token not in STOPWORDS]


def _score_sparse(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    q_counts = Counter(query_tokens)
    d_counts = Counter(doc_tokens)
    overlap = sum(min(q_counts[t], d_counts[t]) for t in q_counts)
    coverage = overlap / max(1, len(q_counts))
    density = overlap / math.sqrt(max(1, len(doc_tokens)))
    return coverage + density


def _score_dense_like(query_tokens: list[str], doc_tokens: list[str]) -> float:
    q_set = set(query_tokens)
    d_set = set(doc_tokens)
    if not q_set or not d_set:
        return 0.0
    return len(q_set & d_set) / len(q_set | d_set)


def _with_scores(query: str, mode: str) -> list[dict]:
    q_tokens = tokenize(query)
    results: list[dict] = []
    for chunk in load_chunks():
        d_tokens = tokenize(chunk["content"])
        sparse = _score_sparse(q_tokens, d_tokens)
        dense = _score_dense_like(q_tokens, d_tokens)
        if mode == "dense":
            score = dense
        elif mode == "sparse":
            score = sparse
        else:
            score = 0.65 * sparse + 0.35 * dense
        item = {**chunk, "score": round(score, 4), "retrieval_source": mode}
        results.append(item)
    return sorted(results, key=lambda item: item["score"], reverse=True)


def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    return _with_scores(query, "dense")[:top_k]


def lexical_search(query: str, top_k: int = 5) -> list[dict]:
    return _with_scores(query, "sparse")[:top_k]


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    q_tokens = tokenize(query)
    q_set = set(q_tokens)
    reranked: list[dict] = []
    for rank, item in enumerate(candidates):
        title_tokens = tokenize(item.get("metadata", {}).get("title", ""))
        content_tokens = tokenize(item.get("content", ""))
        title_bonus = 0.05 * len(q_set & set(title_tokens))
        coverage_bonus = 0.15 * (len(q_set & set(content_tokens)) / max(1, len(q_set)))
        score = item.get("score", 0.0) + title_bonus + coverage_bonus - (rank * 0.001)
        reranked.append({**item, "score": round(score, 4)})
    return sorted(reranked, key=lambda item: item["score"], reverse=True)[:top_k]


def retrieve(query: str, top_k: int = 5, use_reranking: bool = True, mode: str = "hybrid") -> list[dict]:
    """Retrieve context chunks for a query.

    mode can be "hybrid", "dense", or "sparse".
    """
    if mode == "dense":
        return semantic_search(query, top_k)
    if mode == "sparse":
        return lexical_search(query, top_k)

    candidates = _with_scores(query, "hybrid")[: max(top_k * 3, top_k)]
    return rerank(query, candidates, top_k) if use_reranking else candidates[:top_k]
