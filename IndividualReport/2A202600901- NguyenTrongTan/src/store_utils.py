"""
Shared vector store and corpus utilities for Tasks 4–6.
"""

import os
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"
STANDARDIZED_DIR = DATA_DIR / "standardized"
CHROMA_DIR = DATA_DIR / "chroma_db"
COLLECTION_NAME = "DrugLawDocs"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
VECTOR_STORE = os.getenv("VECTOR_STORE", "chromadb")

_embedding_fn = None
_chroma_collection = None
_corpus_chunks: list[dict] = []
_bm25_index = None


def get_repo_env_path() -> Path:
    return Path(__file__).resolve().parents[3] / ".env"


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(
        r"[^\w\sàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]",
        " ",
        text,
    )
    return [t for t in text.split() if t]


class _TfidfEmbeddingFunction:
    """Offline embedding fallback using TF-IDF vectors."""

    def __init__(self):
        self._vectorizer = None
        self._fitted = False

    def _fit(self, texts: list[str]):
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus = list(texts)
        if self._vectorizer is not None and self._fitted:
            return
        self._vectorizer = TfidfVectorizer(max_features=EMBEDDING_DIM)
        self._vectorizer.fit(corpus)
        self._fitted = True

    def __call__(self, input: list[str]) -> list[list[float]]:
        import numpy as np

        self._fit(input)
        matrix = self._vectorizer.transform(input).toarray()
        if matrix.shape[1] < EMBEDDING_DIM:
            pad = np.zeros((matrix.shape[0], EMBEDDING_DIM - matrix.shape[1]))
            matrix = np.hstack([matrix, pad])
        return matrix.tolist()


def _get_embedding_function():
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn

    from chromadb.utils import embedding_functions

    try:
        _embedding_fn = embedding_functions.FastEmbedEmbeddingFunction(
            model_name="BAAI/bge-small-en-v1.5",
        )
        _embedding_fn(["warmup"])
        return _embedding_fn
    except Exception:
        pass

    try:
        from sentence_transformers import SentenceTransformer
        SentenceTransformer(EMBEDDING_MODEL)
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
        )
        return _embedding_fn
    except Exception:
        pass

    try:
        _embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        _embedding_fn(["warmup"])
        return _embedding_fn
    except Exception:
        _embedding_fn = _TfidfEmbeddingFunction()
        return _embedding_fn


def embed_texts(texts: list[str]) -> list[list[float]]:
    ef = _get_embedding_function()
    return ef(texts)


def load_documents() -> list[dict]:
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in md_file.parts else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type},
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text,
                    "metadata": {**doc["metadata"], "chunk_index": i},
                })
    return chunks


def _get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is not None:
        return _chroma_collection

    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    _chroma_collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
    return _chroma_collection


def index_to_chromadb(chunks: list[dict]):
    global _corpus_chunks
    _corpus_chunks = chunks

    collection = _get_chroma_collection()
    if collection.count() > 0:
        return collection

    texts = [c["content"] for c in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": c["metadata"].get("source", ""),
            "type": c["metadata"].get("type", ""),
            "chunk_index": c["metadata"].get("chunk_index", 0),
        }
        for c in chunks
    ]

    batch_size = 50
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
    return collection


def index_to_vectorstore(chunks: list[dict]):
    global _corpus_chunks
    _corpus_chunks = chunks

    store = VECTOR_STORE.lower()
    if store == "weaviate":
        try:
            _index_to_weaviate(chunks)
            return
        except Exception:
            pass
    index_to_chromadb(chunks)


def _index_to_weaviate(chunks: list[dict]):
    import weaviate
    from weaviate.classes.config import Configure, Property, DataType

    texts = [c["content"] for c in chunks]
    embeddings = embed_texts(texts)
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb

    client = weaviate.connect_to_local()
    try:
        if client.collections.exists(COLLECTION_NAME):
            client.collections.delete(COLLECTION_NAME)

        collection = client.collections.create(
            name=COLLECTION_NAME,
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="content", data_type=DataType.TEXT),
                Property(name="source", data_type=DataType.TEXT),
                Property(name="doc_type", data_type=DataType.TEXT),
                Property(name="chunk_index", data_type=DataType.INT),
            ],
        )

        with collection.batch.dynamic() as batch:
            for i, chunk in enumerate(chunks):
                batch.add_object(
                    properties={
                        "content": chunk["content"],
                        "source": chunk["metadata"].get("source", ""),
                        "doc_type": chunk["metadata"].get("type", ""),
                        "chunk_index": chunk["metadata"].get("chunk_index", 0),
                    },
                    vector=chunk["embedding"],
                    uuid=weaviate.util.generate_uuid5(f"chunk_{i}"),
                )
    finally:
        client.close()


def ensure_indexed() -> bool:
    collection = _get_chroma_collection()
    if collection.count() > 0:
        return True

    docs = load_documents()
    if not docs:
        return False

    chunks = chunk_documents(docs)
    if not chunks:
        return False

    index_to_vectorstore(chunks)
    return True


def get_corpus_chunks() -> list[dict]:
    global _corpus_chunks
    if _corpus_chunks:
        return _corpus_chunks

    collection = _get_chroma_collection()
    if collection.count() == 0:
        ensure_indexed()

    if collection.count() == 0:
        return []

    data = collection.get(include=["documents", "metadatas"])
    _corpus_chunks = [
        {
            "content": doc,
            "metadata": {
                "source": meta.get("source", ""),
                "type": meta.get("type", ""),
                "chunk_index": meta.get("chunk_index", 0),
            },
        }
        for doc, meta in zip(data["documents"], data["metadatas"])
    ]
    return _corpus_chunks


def get_bm25_index():
    global _bm25_index
    if _bm25_index is not None:
        return _bm25_index, get_corpus_chunks()

    from rank_bm25 import BM25Okapi

    corpus = get_corpus_chunks()
    if not corpus:
        return None, []

    tokenized = [tokenize(c["content"]) for c in corpus]
    _bm25_index = BM25Okapi(tokenized)
    return _bm25_index, corpus


def query_chromadb(query: str, top_k: int) -> list[dict]:
    ensure_indexed()
    collection = _get_chroma_collection()
    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "content": doc,
            "score": max(0.0, 1.0 - dist),
            "metadata": {
                "source": meta.get("source", ""),
                "type": meta.get("type", ""),
                "chunk_index": meta.get("chunk_index", 0),
            },
        })
    output.sort(key=lambda x: x["score"], reverse=True)
    return output
