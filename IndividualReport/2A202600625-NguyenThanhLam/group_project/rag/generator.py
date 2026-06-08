"""Generation with citation for the group RAG chatbot."""

from __future__ import annotations

from group_project.config.settings import (
    DEFAULT_TOP_K,
    MIN_SCORE_FOR_ANSWER,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)
from group_project.rag.retriever import retrieve

SYSTEM_PROMPT = """Bạn là trợ lý RAG trả lời bằng tiếng Việt.
Chỉ sử dụng context được cung cấp. Mỗi ý quan trọng cần có citation dạng [Nguồn].
Nếu context không đủ bằng chứng, hãy nói rõ rằng chưa thể xác minh từ nguồn hiện có."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    if len(chunks) <= 2:
        return chunks
    front = chunks[::2]
    back = list(reversed(chunks[1::2]))
    return front + back


def format_context(chunks: list[dict]) -> str:
    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        title = meta.get("title", f"Document {index}")
        doc_type = meta.get("type", "unknown")
        parts.append(
            f"[Document {index} | Title: {title} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(parts)


def _fallback_answer(query: str, chunks: list[dict]) -> str:
    if not chunks or chunks[0].get("score", 0.0) < MIN_SCORE_FOR_ANSWER:
        return "Tôi chưa thể xác minh thông tin này từ nguồn hiện có."

    lines = ["Dựa trên các nguồn tìm được:"]
    for chunk in chunks[:3]:
        meta = chunk.get("metadata", {})
        source = meta.get("source", "unknown")
        snippet = chunk.get("content", "").strip()
        if len(snippet) > 420:
            snippet = snippet[:420].rsplit(" ", 1)[0] + "..."
        lines.append(f"- {snippet} [{source}]")
    return "\n".join(lines)


def _call_openrouter(query: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Day08 Group RAG Evaluation Pipeline",
        },
    )
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
        temperature=0.2,
        top_p=0.9,
    )
    return response.choices[0].message.content or ""


def generate_with_citation(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    use_reranking: bool = True,
    mode: str = "hybrid",
) -> dict:
    chunks = retrieve(query, top_k=top_k, use_reranking=use_reranking, mode=mode)
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)

    if OPENROUTER_API_KEY:
        try:
            answer = _call_openrouter(query, context)
        except Exception as exc:
            answer = f"Không gọi được OpenRouter, dùng câu trả lời fallback.\n\n{_fallback_answer(query, reordered)}\n\nLỗi: {exc}"
    else:
        answer = _fallback_answer(query, reordered)

    return {
        "answer": answer,
        "sources": reordered,
        "retrieval_source": mode,
        "used_openrouter": bool(OPENROUTER_API_KEY),
    }
