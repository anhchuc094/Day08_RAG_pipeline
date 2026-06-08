"""Task 8 - PageIndex vectorless fallback.

If PAGEINDEX_API_KEY is available this module can be extended to call the real
SDK. For the individual assignment it provides a vectorless local fallback based
on keyword overlap over markdown chunks.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - keeps tests working without dotenv
    def load_dotenv() -> None:
        return None

from .local_rag_utils import build_chunks, keyword_overlap_score

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents() -> list[dict]:
    """Return local documents that would be uploaded to PageIndex."""
    return build_chunks()


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Vectorless retrieval fallback using structural markdown chunks."""
    if top_k <= 0:
        return []

    results = []
    for chunk in build_chunks():
        score = keyword_overlap_score(query, chunk["content"])
        results.append(
            {
                "content": chunk["content"],
                "score": float(score),
                "metadata": chunk.get("metadata", {}),
                "source": "pageindex",
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in pageindex_search("hình phạt ma túy", top_k=3):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
