"""Task 10 - Generation with citations.

This implementation uses a local extractive answer when no LLM API key is
configured. It still follows the RAG steps: retrieve, reorder, format context,
and answer with source citations.
"""

from .task9_retrieval_pipeline import retrieve

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

SYSTEM_PROMPT = """Answer in Vietnamese using only the provided context.
Every factual claim must include a citation such as [source.md].
If evidence is missing, say: I cannot verify this information."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Place the most important chunk first and the second-best near the end."""
    if len(chunks) <= 2:
        return chunks
    reordered = []
    reordered.extend(chunks[0::2])
    reordered.extend(reversed(chunks[1::2]))
    return reordered


def format_context(chunks: list[dict]) -> str:
    """Format chunks with source labels for citation."""
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"source-{index}")
        doc_type = metadata.get("type", "unknown")
        score = chunk.get("score", 0.0)
        parts.append(
            f"[Document {index} | Source: {source} | Type: {doc_type} | Score: {score:.3f}]\n"
            f"{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(parts)


def _citation(chunk: dict) -> str:
    source = chunk.get("metadata", {}).get("source", "unknown-source")
    return f"[{source}]"


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Generate an extractive cited answer from retrieved chunks."""
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "I cannot verify this information",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    best_chunks = reordered[: min(3, len(reordered))]
    answer_parts = []
    for chunk in best_chunks:
        text = " ".join(chunk.get("content", "").split())
        snippet = text[:320].rstrip()
        if len(text) > 320:
            snippet += "..."
        answer_parts.append(f"{snippet} {_citation(chunk)}")

    answer = (
        f"Dựa trên các nguồn đã truy xuất cho câu hỏi '{query}', thông tin liên quan nhất là: "
        + " ".join(answer_parts)
    )

    return {
        "answer": answer,
        "sources": chunks,
        "context": format_context(reordered),
        "retrieval_source": chunks[0].get("source", "hybrid"),
    }


if __name__ == "__main__":
    result = generate_with_citation("Những nghệ sĩ nào liên quan đến ma túy?")
    print(result["answer"])
