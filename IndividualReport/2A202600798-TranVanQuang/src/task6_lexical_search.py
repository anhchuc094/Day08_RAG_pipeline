"""Task 6 - Lexical search with a small BM25 implementation."""

import math
from collections import Counter

from .local_rag_utils import tokenize
from .task4_chunking_indexing import load_or_build_index

K1 = 1.5
B = 0.75


def build_bm25_index(corpus: list[dict]) -> dict:
    """Build BM25 statistics for a corpus of chunks."""
    tokenized = [tokenize(doc["content"]) for doc in corpus]
    doc_freq = Counter()
    term_freqs = []
    lengths = []

    for tokens in tokenized:
        counts = Counter(tokens)
        term_freqs.append(counts)
        lengths.append(len(tokens))
        doc_freq.update(counts.keys())

    total_docs = max(1, len(corpus))
    avgdl = sum(lengths) / total_docs if lengths else 0.0
    idf = {
        term: math.log(1 + (total_docs - freq + 0.5) / (freq + 0.5))
        for term, freq in doc_freq.items()
    }
    return {"corpus": corpus, "term_freqs": term_freqs, "lengths": lengths, "avgdl": avgdl, "idf": idf}


def _score_document(query_tokens: list[str], index: dict, doc_index: int) -> float:
    score = 0.0
    tf = index["term_freqs"][doc_index]
    doc_len = index["lengths"][doc_index] or 1
    avgdl = index["avgdl"] or 1.0

    for token in query_tokens:
        freq = tf.get(token, 0)
        if freq == 0:
            continue
        idf = index["idf"].get(token, 0.0)
        denominator = freq + K1 * (1 - B + B * doc_len / avgdl)
        score += idf * (freq * (K1 + 1)) / denominator
    return score


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Return top_k chunks ranked by BM25 score."""
    if top_k <= 0:
        return []

    corpus = load_or_build_index()
    index = build_bm25_index(corpus)
    query_tokens = tokenize(query)

    scored = []
    for i, chunk in enumerate(corpus):
        score = _score_document(query_tokens, index, i)
        scored.append(
            {
                "content": chunk["content"],
                "score": float(score),
                "metadata": chunk.get("metadata", {}),
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    for result in lexical_search("Điều 248 ma túy", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
