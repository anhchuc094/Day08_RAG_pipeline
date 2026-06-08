"""Task 10 - Generation with citations."""

from .task9_retrieval_pipeline import retrieve

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.2

SYSTEM_PROMPT = (
    "Answer in Vietnamese using only retrieved context. Cite every factual "
    "claim with the source filename in square brackets."
)


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    if len(chunks) <= 2:
        return chunks
    front = chunks[0::2]
    back = list(reversed(chunks[1::2]))
    return front + back


def format_context(chunks: list[dict]) -> str:
    blocks = []
    for number, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", f"source-{number}")
        kind = meta.get("type", "unknown")
        blocks.append(
            f"[{number}] Source: {source} | Type: {kind} | Score: {chunk.get('score', 0.0):.3f}\n"
            f"{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(blocks)


def _source_label(chunk: dict) -> str:
    return chunk.get("metadata", {}).get("source", "unknown-source")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "I cannot verify this information",
            "sources": [],
            "retrieval_source": "none",
        }

    ordered = reorder_for_llm(chunks)
    evidence = []
    for chunk in ordered[:3]:
        text = " ".join(chunk.get("content", "").split())
        snippet = text[:300].rstrip()
        if len(text) > 300:
            snippet += "..."
        evidence.append(f"{snippet} [{_source_label(chunk)}]")

    answer = (
        f"Dua tren nguon da truy xuat cho cau hoi '{query}', cac bang chung lien quan nhat la: "
        + " ".join(evidence)
    )
    return {
        "answer": answer,
        "sources": chunks,
        "context": format_context(ordered),
        "retrieval_source": chunks[0].get("source", "hybrid"),
    }
