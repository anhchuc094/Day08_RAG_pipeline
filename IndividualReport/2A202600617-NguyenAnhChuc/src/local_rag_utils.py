"""Shared helpers for Nguyen Anh Chuc's individual RAG pipeline.

The implementation is intentionally local and deterministic so the assignment
can be graded without API keys, Docker, or network access.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
STANDARDIZED_DIR = DATA_DIR / "standardized"
INDEX_PATH = DATA_DIR / "local_vector_index.json"

TOKEN_PATTERN = re.compile(r"[0-9A-Za-z_]+|[^\W\d_]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Lowercase tokenizer that works acceptably for Vietnamese text."""
    return TOKEN_PATTERN.findall(text.lower())


def read_standardized_markdown() -> list[dict]:
    """Load every markdown document in data/standardized."""
    docs: list[dict] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if path.name.startswith("."):
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        kind = "legal" if "legal" in path.parts else "news"
        docs.append(
            {
                "content": text,
                "metadata": {
                    "source": path.name,
                    "path": str(path.relative_to(PROJECT_DIR)),
                    "type": kind,
                },
            }
        )
    return docs


def paragraph_aware_chunks(text: str, size: int, overlap: int) -> list[str]:
    """Split text by paragraphs/sentences while keeping a maximum char budget."""
    cleaned = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    stride = max(1, size - overlap)
    while start < len(cleaned):
        stop = min(len(cleaned), start + size)
        if stop < len(cleaned):
            paragraph_break = cleaned.rfind("\n\n", start, stop)
            sentence_break = cleaned.rfind(". ", start, stop)
            boundary = max(paragraph_break, sentence_break)
            if boundary > start + size // 2:
                stop = boundary + 1

        chunk = cleaned[start:stop].strip()
        if chunk:
            chunks.append(chunk)
        if stop >= len(cleaned):
            break
        start = max(0, stop - overlap)
        if start >= stop:
            start = stop
    return chunks


def stable_embedding(text: str, dimensions: int) -> list[float]:
    """Create a small signed hashing embedding."""
    vector = [0.0] * dimensions
    for token, count in Counter(tokenize(text)).items():
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign * (1.0 + math.log(count))

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def dot(left: list[float], right: list[float]) -> float:
    """Cosine for normalized vectors."""
    return float(sum(a * b for a, b in zip(left, right)))


def overlap(query: str, text: str) -> float:
    """Simple lexical relevance score in the range 0..1-ish."""
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0
    counts = Counter(tokenize(text))
    matched = sum(1 for token in query_tokens if counts[token] > 0)
    frequency = sum(min(counts[token], 3) for token in query_tokens) / (3 * len(query_tokens))
    return 0.75 * matched / len(query_tokens) + 0.25 * frequency


def save_index(items: list[dict]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def load_saved_index() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []
