# Bao cao ca nhan - Nguyen Anh Chuc

MSSV: 2A202600617

Thu muc nay chua phan bai ca nhan Day 08 RAG Pipeline, gom day du Task 1 den Task 10.

## Cau truc

```text
2A202600617-NguyenAnhChuc/
|-- data/
|   |-- landing/
|   |   |-- legal/
|   |   `-- news/
|   |-- standardized/
|   |   |-- legal/
|   |   `-- news/
|   `-- local_vector_index.json
|-- src/
|   |-- task1_collect_legal_docs.py
|   |-- task2_crawl_news.py
|   |-- task3_convert_markdown.py
|   |-- task4_chunking_indexing.py
|   |-- task5_semantic_search.py
|   |-- task6_lexical_search.py
|   |-- task7_reranking.py
|   |-- task8_pageindex_vectorless.py
|   |-- task9_retrieval_pipeline.py
|   |-- task10_generation.py
|   `-- local_rag_utils.py
|-- tests/
`-- requirements.txt
```

## Noi dung da hoan thanh

| Task | Noi dung | Trang thai |
|---|---|---|
| 1 | Thu thap toi thieu 3 van ban phap luat ve ma tuy | Hoan thanh |
| 2 | Crawl/lap du lieu toi thieu 5 bai bao lien quan nghe si va ma tuy | Hoan thanh |
| 3 | Chuyen du lieu sang Markdown trong `data/standardized/` | Hoan thanh |
| 4 | Chunking va local indexing bang hashing embedding | Hoan thanh |
| 5 | Semantic search tren local vector index | Hoan thanh |
| 6 | Lexical search theo BM25-like scoring | Hoan thanh |
| 7 | Reranking bang ket hop overlap va score goc | Hoan thanh |
| 8 | PageIndex vectorless fallback local | Hoan thanh |
| 9 | Retrieval pipeline hybrid + fallback | Hoan thanh |
| 10 | Generation co citation va reorder context | Hoan thanh |

## Cach chay test

Tu trong thu muc nay:

```bash
python -m pytest tests/test_individual.py -v
```

Neu may khong co Python tren PATH, can kich hoat dung moi truong Python truoc khi chay lenh test.
