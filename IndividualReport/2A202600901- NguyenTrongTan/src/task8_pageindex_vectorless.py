"""
Task 8 — PageIndex Vectorless RAG.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .store_utils import STANDARDIZED_DIR, get_bm25_index, get_repo_env_path, tokenize

load_dotenv(get_repo_env_path())

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")


def _is_valid_pageindex_key(key: str) -> bool:
    if not key or key in ("pi_xxx", "xxx"):
        return False
    return True


def _mock_pageindex_search(query: str, top_k: int) -> list[dict]:
    bm25, corpus = get_bm25_index()
    if bm25 is None or not corpus:
        docs = []
        if STANDARDIZED_DIR.exists():
            for md_file in STANDARDIZED_DIR.rglob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                docs.append({
                    "content": content[:1500],
                    "metadata": {"source": md_file.name, "type": md_file.parent.name},
                })
        if not docs:
            return [{
                "content": "Không tìm thấy tài liệu trong kho dữ liệu.",
                "score": 0.1,
                "metadata": {"source": "fallback"},
                "source": "pageindex",
            }]
        q_tokens = set(tokenize(query))
        scored = []
        for doc in docs:
            overlap = len(q_tokens & set(tokenize(doc["content"]))) if q_tokens else 0
            scored.append((overlap, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for i, (score, doc) in enumerate(scored[:top_k]):
            results.append({
                "content": doc["content"],
                "score": max(0.1, score / max(len(q_tokens), 1)),
                "metadata": doc["metadata"],
                "source": "pageindex",
            })
        return results

    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)
    import numpy as np
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        if scores[idx] > 0 or len(results) == 0:
            results.append({
                "content": corpus[idx]["content"],
                "score": float(scores[idx]) if scores[idx] > 0 else 0.1,
                "metadata": corpus[idx]["metadata"],
                "source": "pageindex",
            })
    return results[:top_k] if results else _mock_pageindex_search(query, top_k)


def upload_documents():
    if not _is_valid_pageindex_key(PAGEINDEX_API_KEY):
        print("  ⚠ PageIndex API key không hợp lệ — bỏ qua upload, dùng mock search.")
        return

    try:
        from pageindex import PageIndex
        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        for md_file in STANDARDIZED_DIR.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            pi.upload(
                content=content,
                metadata={"filename": md_file.name, "type": md_file.parent.name},
            )
            print(f"  ✓ Uploaded: {md_file.name}")
    except Exception as e:
        print(f"  ⚠ PageIndex upload failed: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    if not _is_valid_pageindex_key(PAGEINDEX_API_KEY):
        return _mock_pageindex_search(query, top_k)

    try:
        from pageindex import PageIndex
        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        results = pi.query(query=query, top_k=top_k)
        return [
            {
                "content": r.text,
                "score": r.score,
                "metadata": r.metadata,
                "source": "pageindex",
            }
            for r in results
        ]
    except Exception:
        return _mock_pageindex_search(query, top_k)


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
    else:
        upload_documents()
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
