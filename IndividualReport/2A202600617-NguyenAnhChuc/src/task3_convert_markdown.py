"""Task 3 - Convert landing data into markdown.

News JSON is converted directly. Legal PDFs are represented by existing
standardized markdown files in this submitted package; the function can also
create short metadata markdown if a PDF has no extracted text yet.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
LANDING_DIR = PROJECT_DIR / "data" / "landing"
STANDARDIZED_DIR = PROJECT_DIR / "data" / "standardized"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def convert_news_articles() -> list[Path]:
    outputs = []
    for source_path in sorted((LANDING_DIR / "news").glob("*.json")):
        data = json.loads(source_path.read_text(encoding="utf-8"))
        markdown = (
            f"# {data.get('title', source_path.stem)}\n\n"
            f"**Source:** {data.get('source', 'Unknown')}\n\n"
            f"**URL:** {data.get('url', 'N/A')}\n\n"
            f"**Crawled:** {data.get('crawl_date', 'N/A')}\n\n"
            "---\n\n"
            f"{data.get('content') or data.get('content_markdown', '')}"
        )
        output_path = STANDARDIZED_DIR / "news" / f"{source_path.stem}.md"
        _write(output_path, markdown)
        outputs.append(output_path)
    return outputs


def convert_legal_documents() -> list[Path]:
    outputs = []
    for source_path in sorted((LANDING_DIR / "legal").iterdir()):
        if source_path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        output_path = STANDARDIZED_DIR / "legal" / f"{source_path.stem}.md"
        if not output_path.exists():
            markdown = (
                f"# {source_path.stem}\n\n"
                f"**Source file:** {source_path.name}\n\n"
                "Van ban phap luat ve phong, chong ma tuy duoc thu thap cho "
                "pipeline RAG ca nhan. Noi dung chi tiet can doi chieu voi file "
                "goc trong data/landing/legal."
            )
            _write(output_path, markdown)
        outputs.append(output_path)
    return outputs


def convert_all() -> list[Path]:
    return convert_legal_documents() + convert_news_articles()


if __name__ == "__main__":
    for path in convert_all():
        print(path)
