# Bài Tập Nhóm - RAG Evaluation Pipeline

## Sản Phẩm Đã Chọn

Theo README gốc, bài nhóm chỉ cần xây dựng **1 trong 2 sản phẩm**. Nhóm chọn:

```text
Yêu cầu 2: RAG Evaluation Pipeline
```

Mục tiêu là đánh giá pipeline RAG bằng golden dataset, 4 nhóm metric và A/B comparison giữa ít nhất 2 cấu hình retrieval/generation.

Framework được chọn theo README mẫu:

```text
DeepEval
```

## Cấu Trúc Thư Mục

```text
group_project/
├── config/
│   └── settings.py
├── data/
│   └── sample_corpus.json
├── rag/
│   ├── documents.py
│   ├── generator.py
│   └── retriever.py
├── evaluation/
│   ├── golden_dataset.json
│   ├── eval_pipeline.py
│   └── results.md
├── phan_cong_nhom.md
└── README.md
```

Code nhóm không sửa hoặc phụ thuộc trực tiếp vào folder `src/`. Module `group_project/rag` chỉ đóng vai trò pipeline tối giản để chạy evaluation.

## Dữ Liệu

Pipeline ưu tiên đọc dữ liệu trong:

```text
data/standardized/
```

Các định dạng đang được hỗ trợ:

- `.md`
- `.txt`
- `.json`
- `.doc`
- `.docx`
- `.pdf`

Với `.doc/.docx/.pdf`, loader sẽ thử dùng `markitdown`. Nếu chưa đọc được dữ liệu thật, pipeline fallback sang:

```text
group_project/data/sample_corpus.json
```

Hiện `data/standardized/` đã có 3 file `.doc`, nên phần loader đã được sửa để scan thêm định dạng này.

## Golden Dataset

File:

```text
group_project/evaluation/golden_dataset.json
```

Mỗi item có format:

```json
{
  "id": "qa_001",
  "question": "Câu hỏi",
  "expected_answer": "Câu trả lời kỳ vọng",
  "expected_chunks": ["chunk/evidence cần được truy xuất"]
}
```

Dataset hiện có 15 Q&A.

## Evaluation Framework Và Metrics

Script ưu tiên dùng DeepEval theo code mẫu trong README gốc:

- `FaithfulnessMetric`
- `AnswerRelevancyMetric`
- `ContextualRecallMetric`
- `ContextualPrecisionMetric`

Nếu môi trường chưa cài DeepEval hoặc thiếu API key cho LLM judge, script tự fallback sang metric offline để vẫn tạo được report demo. Khi nộp/chạy chính thức, nên chạy được DeepEval.

4 metric bắt buộc:

| Metric | Ý nghĩa |
|---|---|
| Faithfulness | Câu trả lời có bám vào retrieved context không |
| Answer Relevance | Câu trả lời có liên quan câu hỏi và expected answer không |
| Context Recall | Context có lấy được đủ evidence kỳ vọng không |
| Context Precision | Context truy xuất có tập trung vào evidence cần thiết không |

## A/B Comparison

Script so sánh 2 cấu hình:

| Config | Mô tả |
|---|---|
| Hybrid + Reranking | Kết hợp sparse/dense-like retrieval và reranking |
| Dense Only | Chỉ dùng dense-like token similarity, không reranking |

## Cách Chạy

### 1. Chuẩn bị môi trường

```bash
pip install -r requirements.txt
```

DeepEval đã có trong `requirements.txt`:

```text
deepeval>=1.0.0
```

Nếu máy dùng virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Kiểm tra dữ liệu

Đảm bảo các file dữ liệu đã nằm trong:

```text
data/standardized/
```

Hiện project có 3 file `.doc` trong thư mục này. Evaluation loader sẽ thử đọc bằng `markitdown`; nếu đọc không được, pipeline tự dùng corpus mẫu để vẫn chạy được.

### 3. Chạy evaluation

```bash
python -m group_project.evaluation.eval_pipeline
```

Kết quả được ghi vào:

```text
group_project/evaluation/results.md
```

### 4. Kiểm tra golden dataset

Golden dataset phải là câu hỏi thuộc đề tài pháp luật ma túy. Mỗi item cần có:

- `id`
- `question`
- `expected_answer`
- `expected_chunks`

Hiện dataset có 15 câu hỏi đúng domain.

## Phân Công Công Việc

Chi tiết nằm trong:

```text
group_project/phan_cong_nhom.md
```

Tóm tắt:

| Thành viên | Vai trò | Nhiệm vụ | Deliverable | Branch gợi ý |
|---|---|---|---|---|
| Thành viên 1 | Data Lead | Chuẩn hóa dữ liệu, convert `.doc` sang `.md` | `data/standardized/*.md`, `group_project/tools/convert_doc_to_md.ps1` | `feature/group-data` |
| Thành viên 2 | Retrieval Lead | Loader, chunking, retrieval, cấu hình A/B | `group_project/rag/documents.py`, `group_project/rag/retriever.py`, `group_project/config/settings.py` | `feature/group-retrieval` |
| Thành viên 3 | RAG Runner Lead | Generation có citation, format context | `group_project/rag/generator.py`, `group_project/data/sample_corpus.json` | `feature/group-rag-runner` |
| Thành viên 4 | Evaluation và Git Lead | Golden dataset, DeepEval, report, README | `group_project/evaluation/`, `group_project/README.md`, `group_project/phan_cong_nhom.md` | `feature/group-evaluation` |

Mỗi thành viên cần có ít nhất 1 commit riêng trên GitHub. Sau khi push, cập nhật username và commit hash trong `group_project/phan_cong_nhom.md`.

## Checklist

- [x] Chọn 1 sản phẩm: RAG Evaluation Pipeline.
- [x] Golden dataset có 15 Q&A.
- [x] Mỗi Q&A có `id`.
- [x] Mỗi Q&A có `expected_chunks`.
- [x] Có 4 metric: faithfulness, answer relevance, context recall, context precision.
- [x] Có A/B comparison ít nhất 2 configs.
- [x] Có report output trong `results.md`.
- [x] Có sử dụng code mẫu DeepEval trong `eval_pipeline.py`.
