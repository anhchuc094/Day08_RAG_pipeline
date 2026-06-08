"""Task 4 - Chunking and local indexing."""

from __future__ import annotations

from .local_rag_utils import paragraph_aware_chunks, read_standardized_markdown, save_index, stable_embedding

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "paragraph-aware-recursive"
EMBEDDING_MODEL = "signed-hashing-local"
EMBEDDING_DIM = 384
VECTOR_STORE = "json-local"


def load_documents() -> list[dict]:
    return read_standardized_markdown()


def chunk_documents(documents: list[dict]) -> list[dict]:
    chunks = []
    for doc in documents:
        for index, text in enumerate(paragraph_aware_chunks(doc["content"], CHUNK_SIZE, CHUNK_OVERLAP)):
            chunks.append(
                {
                    "content": text,
                    "metadata": {**doc["metadata"], "chunk_index": index},
                }
            )
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    return [
        {**chunk, "embedding": stable_embedding(chunk["content"], EMBEDDING_DIM)}
        for chunk in chunks
    ]


def index_to_vectorstore(chunks: list[dict]) -> list[dict]:
    save_index(chunks)
    return chunks


def build_index() -> list[dict]:
    return index_to_vectorstore(embed_chunks(chunk_documents(load_documents())))


def load_or_build_index() -> list[dict]:
    # Rebuild from this folder's markdown every time so the submitted code does
    # not depend on a pre-copied index artifact.
    return build_index()


def run_pipeline() -> list[dict]:
    index = build_index()
    print(f"Indexed {len(index)} chunks with {EMBEDDING_MODEL}")
    return index


if __name__ == "__main__":
    run_pipeline()
