# Phân Công Công Việc Nhóm - RAG Evaluation Pipeline

## 1. Sản Phẩm Nhóm Đã Chọn

Theo README gốc, bài nhóm chỉ cần chọn **1 trong 2 sản phẩm**. Nhóm chọn:

```text
Yêu cầu 2: RAG Evaluation Pipeline
```

Mục tiêu:

- Tạo golden dataset tối thiểu 15 Q&A về pháp luật ma túy.
- Chạy evaluation với 4 metric: Faithfulness, Answer Relevance, Context Recall, Context Precision.
- Sử dụng framework mẫu: **DeepEval**.
- So sánh A/B ít nhất 2 cấu hình retrieval/generation.
- Viết report kết quả trong `group_project/evaluation/results.md`.
- Mỗi thành viên phải có ít nhất 1 commit trên GitHub.

## 2. Kiến Trúc Phần Nhóm

```text
data/standardized/*.md
  |
  v
group_project/rag/documents.py
  |
  v
group_project/rag/retriever.py
  |
  v
group_project/rag/generator.py
  |
  v
group_project/evaluation/eval_pipeline.py
  |
  v
group_project/evaluation/results.md
```

## 3. Phân Công Cho 4 Thành Viên

| Thành viên | Vai trò | Nhiệm vụ chính | File/Deliverable | Branch gợi ý | Commit gợi ý |
|---|---|---|---|---|---|
| Quang | Data Lead | Chuẩn hóa dữ liệu, convert `.doc` sang `.md`, kiểm tra corpus thật | `data/standardized/*.md`, `group_project/tools/convert_doc_to_md.ps1` | `feature/group-data` | `feat: add standardized markdown corpus` |
| Chức | Retrieval Lead | Viết loader/chunking/retrieval, cấu hình A/B retrieval | `group_project/rag/documents.py`, `group_project/rag/retriever.py`, `group_project/config/settings.py` | `feature/group-retrieval` | `feat: add group retrieval pipeline` |
| Lam | RAG Runner Lead | Viết generation có citation, format context, kết nối retriever với evaluation | `group_project/rag/generator.py`, `group_project/data/sample_corpus.json` | `feature/group-rag-runner` | `feat: add citation generation runner` |
| Tấn | Evaluation và Git Lead | Tạo golden dataset, implement DeepEval theo code mẫu, A/B comparison, report, README | `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/eval_pipeline.py`, `group_project/evaluation/results.md`, `group_project/README.md`, `group_project/phan_cong_nhom.md` | `feature/group-evaluation` | `feat: add deepeval evaluation pipeline` |

## 4. Checklist Commit GitHub

Mỗi thành viên cần có ít nhất 1 commit riêng trên GitHub. Không nên để một người commit toàn bộ phần nhóm.

| Thành viên | GitHub username | Branch | Commit hash | Trạng thái |
|---|---|---|---|---|
| Thành viên 1 | `<github-user-1>` | `feature/group-data` | `<commit-hash>` | Chưa cập nhật |
| Thành viên 2 | `<github-user-2>` | `feature/group-retrieval` | `<commit-hash>` | Chưa cập nhật |
| Thành viên 3 | `<github-user-3>` | `feature/group-rag-runner` | `<commit-hash>` | Chưa cập nhật |
| Thành viên 4 | `<github-user-4>` | `feature/group-evaluation` | `<commit-hash>` | Chưa cập nhật |

Sau khi mỗi bạn push code, cập nhật bảng trên bằng username và commit hash thật.

## 5. Quy Trình Làm Việc Git

Mỗi thành viên tạo branch riêng từ `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/group-data
```

Sau khi sửa phần của mình:

```bash
git status
git add <file-cua-minh>
git commit -m "feat: add standardized markdown corpus"
git push origin feature/group-data
```

Tạo Pull Request trên GitHub:

- Mô tả phần đã làm.
- Ghi rõ file đã sửa.
- Ghi cách test.
- Dẫn link commit của thành viên.

## 6. Gợi Ý Commit Theo Từng Người

### Thành viên 1 - Data Lead

```bash
git checkout -b feature/group-data
git add data/standardized/*.md group_project/tools/convert_doc_to_md.ps1
git commit -m "feat: add standardized markdown corpus"
git push origin feature/group-data
```

### Thành viên 2 - Retrieval Lead

```bash
git checkout -b feature/group-retrieval
git add group_project/rag/documents.py group_project/rag/retriever.py group_project/config/settings.py
git commit -m "feat: add group retrieval pipeline"
git push origin feature/group-retrieval
```

### Thành viên 3 - RAG Runner Lead

```bash
git checkout -b feature/group-rag-runner
git add group_project/rag/generator.py group_project/data/sample_corpus.json
git commit -m "feat: add citation generation runner"
git push origin feature/group-rag-runner
```

### Thành viên 4 - Evaluation và Git Lead

```bash
git checkout -b feature/group-evaluation
git add group_project/evaluation group_project/README.md group_project/phan_cong_nhom.md
git commit -m "feat: add deepeval evaluation pipeline"
git push origin feature/group-evaluation
```

## 7. Deliverable Cuối

- [x] `group_project/evaluation/golden_dataset.json` có 15+ Q&A đúng đề tài.
- [x] `group_project/evaluation/eval_pipeline.py` dùng DeepEval theo code mẫu.
- [x] Có A/B comparison: `Hybrid + Reranking` và `Dense Only`.
- [x] `group_project/evaluation/results.md` là nơi ghi kết quả.
- [x] `group_project/README.md` mô tả kiến trúc, framework, cách chạy.
- [x] `group_project/phan_cong_nhom.md` mô tả phân công 4 người.
- [ ] Mỗi thành viên có ít nhất 1 commit riêng trên GitHub.
