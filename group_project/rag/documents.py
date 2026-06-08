"""Document loading and chunking for the group RAG pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from group_project.config.settings import CHUNK_OVERLAP, CHUNK_SIZE, SAMPLE_CORPUS_PATH, STANDARDIZED_DIR

SUPPORTED_STANDARDIZED_SUFFIXES = {".md", ".txt", ".json", ".doc", ".docx", ".pdf"}


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = " ".join(text.split())
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += step
    return chunks


def _read_standardized_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="ignore").strip()

    if suffix == ".json":
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip()
        if isinstance(data, dict):
            fields = [data.get("title", ""), data.get("content", ""), data.get("content_markdown", "")]
            return "\n\n".join(str(field) for field in fields if field).strip()
        return raw.strip()

    try:
        from markitdown import MarkItDown

        return MarkItDown().convert(str(path)).text_content.strip()
    except Exception:
        return ""


def _load_standardized_documents() -> list[dict]:
    documents: list[dict] = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for path in STANDARDIZED_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_STANDARDIZED_SUFFIXES:
            continue
        content = _read_standardized_file(path)
        if not content:
            continue
        rel = path.relative_to(STANDARDIZED_DIR)
        doc_type = rel.parts[0] if len(rel.parts) > 1 else "standardized"
        documents.append(
            {
                "title": path.stem,
                "source": str(rel).replace("\\", "/"),
                "type": doc_type,
                "content": content,
            }
        )
    return documents


def _load_sample_documents() -> list[dict]:
    if not SAMPLE_CORPUS_PATH.exists():
        return []
    return json.loads(SAMPLE_CORPUS_PATH.read_text(encoding="utf-8"))


def load_documents() -> list[dict]:
    """Load standardized files, falling back to the demo corpus."""
    docs = _load_standardized_documents()
    return docs if docs else _load_sample_documents()


def load_chunks() -> list[dict]:
    """Return chunk dictionaries with content, score placeholder and metadata."""
    chunks: list[dict] = []
    for doc in load_documents():
        for index, text in enumerate(_chunk_text(doc["content"])):
            chunks.append(
                {
                    "content": text,
                    "metadata": {
                        "title": doc.get("title", "Untitled"),
                        "source": doc.get("source", "unknown"),
                        "type": doc.get("type", "unknown"),
                        "chunk_index": index,
                    },
                }
            )
    return chunks
