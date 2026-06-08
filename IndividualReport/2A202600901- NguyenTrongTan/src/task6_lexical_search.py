"""
Task 6 — Lexical Search Module (BM25).
"""

import numpy as np

from .store_utils import get_bm25_index, tokenize

CORPUS: list[dict] = []


def build_bm25_index(corpus: list[dict]):
    global CORPUS
    from rank_bm25 import BM25Okapi

    CORPUS = corpus
    tokenized_corpus = [tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    bm25, corpus = get_bm25_index()
    if bm25 is None or not corpus:
        return []

    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({
                "content": corpus[idx]["content"],
                "score": float(scores[idx]),
                "metadata": corpus[idx]["metadata"],
            })
    return results


if __name__ == "__main__":
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
