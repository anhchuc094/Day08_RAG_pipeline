# RAG Evaluation Results

## A/B Comparison

| Config | Faithfulness | Answer Relevance | Context Recall | Context Precision | Average |
|---|---:|---:|---:|---:|---:|
| Hybrid + Reranking | 0.941 | 0.899 | 0.77 | 0.889 | 0.875 |
| Dense Only | 0.878 | 0.753 | 0.616 | 0.778 | 0.756 |

## Best Config

Best average score: **Hybrid + Reranking**.

## Bottom 3 Questions

| ID | Question | Avg | Main Issue |
|---|---|---:|---|
| qa_011 | Nghị định 163/2026/NĐ-CP quy định chi tiết và hướng dẫn thi hành những nhóm nội dung nào? | 0.656 | Cần bổ sung context hoặc tăng độ phủ retrieval |
| qa_007 | Cai nghiện ma túy là quá trình như thế nào? | 0.714 | Cần bổ sung context hoặc tăng độ phủ retrieval |
| qa_005 | Phòng, chống ma túy được hiểu là gì? | 0.773 | Cần bổ sung context hoặc tăng độ phủ retrieval |

## Recommendations

- Chuẩn hóa `expected_chunks` sát câu chữ trong các file Markdown thật.
- Giảm `top_k` hoặc chunk size nếu context precision còn thấp.
- Dùng embedding thật và vector store khi môi trường Python/dependencies đã sẵn sàng.
- Giữ câu trả lời có citation ngắn, rõ và chỉ dựa vào context.
