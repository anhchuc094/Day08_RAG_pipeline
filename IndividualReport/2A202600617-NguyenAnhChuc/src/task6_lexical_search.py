"""Task 6 - BM25 lexical search."""

import math
from collections import Counter

from .local_rag_utils import tokenize
from .task4_chunking_indexing import load_or_build_index

K1 = 1.4
B = 0.72


def _prepare(corpus: list[dict]) -> dict:
    token_lists = [tokenize(item["content"]) for item in corpus]
    term_freqs = [Counter(tokens) for tokens in token_lists]
    lengths = [len(tokens) for tokens in token_lists]
    doc_freq = Counter()
    for counts in term_freqs:
        doc_freq.update(counts.keys())
    n_docs = max(1, len(corpus))
    avg_len = sum(lengths) / n_docs if lengths else 1.0
    idf = {
        token: math.log(1 + (n_docs - freq + 0.5) / (freq + 0.5))
        for token, freq in doc_freq.items()
    }
    return {"tf": term_freqs, "lengths": lengths, "avg_len": avg_len, "idf": idf}


def _bm25(tokens: list[str], stats: dict, index: int) -> float:
    score = 0.0
    doc_len = stats["lengths"][index] or 1
    for token in tokens:
        freq = stats["tf"][index].get(token, 0)
        if not freq:
            continue
        denominator = freq + K1 * (1 - B + B * doc_len / stats["avg_len"])
        score += stats["idf"].get(token, 0.0) * freq * (K1 + 1) / denominator
    return float(score)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    if top_k <= 0:
        return []
    corpus = load_or_build_index()
    stats = _prepare(corpus)
    query_tokens = tokenize(query)
    results = []
    for index, item in enumerate(corpus):
        results.append(
            {
                "content": item["content"],
                "score": _bm25(query_tokens, stats, index),
                "metadata": item.get("metadata", {}),
            }
        )
    results.sort(key=lambda row: row["score"], reverse=True)
    return results[:top_k]
