"""Task 4 - Chunking and local indexing.

Chunking strategy: recursive character-style splitting. It is conservative for
mixed legal/news markdown because it prefers paragraph and sentence boundaries
while still enforcing a hard size budget.

Embedding model: local hashing embedding, 384 dimensions. In a production demo
this can be swapped for BAAI/bge-m3, but hashing keeps the individual pipeline
deterministic and runnable without downloading large models.
"""

import json
from pathlib import Path

from .local_rag_utils import build_chunks, hashed_embedding, load_markdown_documents

PROJECT_DIR = Path(__file__).parent.parent
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"
INDEX_PATH = PROJECT_DIR / "data" / "local_vector_index.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "local-hashing-tfidf"
EMBEDDING_DIM = 384

VECTOR_STORE = "local-json"


def load_documents() -> list[dict]:
    """Read all markdown files from data/standardized/."""
    return load_markdown_documents()


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Split documents into bounded chunks with inherited metadata."""
    from .local_rag_utils import split_text

    chunks = []
    for doc in documents:
        for index, text in enumerate(split_text(doc["content"], CHUNK_SIZE, CHUNK_OVERLAP)):
            chunks.append(
                {
                    "content": text,
                    "metadata": {**doc["metadata"], "chunk_index": index},
                }
            )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Attach deterministic local embeddings to every chunk."""
    embedded = []
    for chunk in chunks:
        item = {**chunk, "embedding": hashed_embedding(chunk["content"], EMBEDDING_DIM)}
        embedded.append(item)
    return embedded


def index_to_vectorstore(chunks: list[dict]) -> Path:
    """Persist the local vector index as JSON for later search modules."""
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return INDEX_PATH


def load_or_build_index() -> list[dict]:
    """Load existing local index or build it from markdown files."""
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    chunks = embed_chunks(chunk_documents(load_documents()))
    index_to_vectorstore(chunks)
    return chunks


def run_pipeline() -> None:
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"Loaded {len(docs)} documents")
    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")
    chunks = embed_chunks(chunks)
    path = index_to_vectorstore(chunks)
    print(f"Indexed to {path}")


if __name__ == "__main__":
    run_pipeline()
