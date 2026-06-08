"""
Task 4 — Chunking & Indexing vào Vector Store.
"""

from pathlib import Path

from .store_utils import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    STANDARDIZED_DIR,
    VECTOR_STORE,
    chunk_documents as _chunk_documents,
    embed_texts,
    index_to_vectorstore as _index_to_vectorstore,
    load_documents as _load_documents,
)

CHUNKING_METHOD = "recursive"


def load_documents() -> list[dict]:
    return _load_documents()


def chunk_documents(documents: list[dict]) -> list[dict]:
    return _chunk_documents(documents)


def embed_chunks(chunks: list[dict]) -> list[dict]:
    texts = [c["content"] for c in chunks]
    try:
        embeddings = embed_texts(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb
    except Exception:
        for chunk in chunks:
            chunk["embedding"] = []
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    _index_to_vectorstore(chunks)


def run_pipeline():
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
