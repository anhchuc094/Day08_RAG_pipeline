"""Small local utilities shared by the individual RAG tasks.

The assignment recommends production tools such as Weaviate, embeddings, and
PageIndex. For the individual automated tests we keep a deterministic local
fallback so the pipeline works without cloud accounts or API keys.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"

TOKEN_RE = re.compile(r"[\wÀ-ỹ]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def load_markdown_documents() -> list[dict]:
    documents = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_file.name.startswith("."):
            continue
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue
        doc_type = "legal" if "legal" in md_file.parts else "news"
        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "path": str(md_file.relative_to(PROJECT_DIR)),
                    "type": doc_type,
                },
            }
        )
    return documents


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not text:
        return []

    chunks = []
    start = 0
    step = max(1, chunk_size - chunk_overlap)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        if end < len(text):
            boundary = max(text.rfind("\n\n", start, end), text.rfind(". ", start, end))
            if boundary > start + int(chunk_size * 0.5):
                end = boundary + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - chunk_overlap)
        if start >= end:
            start = end
    return chunks


def build_chunks(chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    chunks = []
    for doc in load_markdown_documents():
        for index, chunk_text in enumerate(split_text(doc["content"], chunk_size, chunk_overlap)):
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {**doc["metadata"], "chunk_index": index},
                }
            )
    return chunks


def hashed_embedding(text: str, dim: int = 384) -> list[float]:
    vector = [0.0] * dim
    for token, count in Counter(tokenize(text)).items():
        digest = hashlib.md5(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(value * value for value in vector))
    if norm:
        vector = [value / norm for value in vector]
    return vector


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def keyword_overlap_score(query: str, text: str) -> float:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0
    text_counts = Counter(tokenize(text))
    hits = sum(1 for token in query_tokens if text_counts[token] > 0)
    frequency_bonus = sum(min(text_counts[token], 3) for token in query_tokens) / (3 * len(query_tokens))
    return (hits / len(query_tokens)) * 0.8 + frequency_bonus * 0.2
