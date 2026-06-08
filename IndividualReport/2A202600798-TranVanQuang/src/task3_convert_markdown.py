"""
Task 3 - Convert all files in data/landing/ to Markdown.

Legal PDF/DOC/DOCX files are converted with MarkItDown.
News JSON files are converted manually so their metadata is preserved.
"""

import json
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOC/DOCX files in data/landing/legal/ to markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() not in {".pdf", ".docx", ".doc"}:
            continue

        print(f"Converting legal file: {filepath.name}")
        result = md.convert(str(filepath))
        content = result.text_content.strip()
        if len(content) < 200:
            content = (
                f"# {filepath.stem}\n\n"
                f"**Source file:** {filepath.name}\n\n"
                "**Document type:** legal\n\n"
                "This legal document was collected for the Day 08 RAG pipeline "
                "dataset about Vietnamese drug prevention law and controlled "
                "substances. MarkItDown could not extract enough readable text "
                "from the original PDF, so this fallback markdown keeps the file "
                "represented in the standardized corpus. Use the original PDF in "
                "data/landing/legal for manual review and citation checks.\n"
            )
        output_path = output_dir / f"{filepath.stem}.md"
        output_path.write_text(content + "\n", encoding="utf-8")
        print(f"  Saved: {output_path}")


def convert_news_articles() -> None:
    """Convert crawled JSON articles in data/landing/news/ to markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() != ".json":
            continue

        print(f"Converting news file: {filepath.name}")
        data = json.loads(filepath.read_text(encoding="utf-8"))

        title = data.get("title", "Unknown title")
        source = data.get("source", "Unknown source")
        url = data.get("url", "N/A")
        crawl_date = data.get("crawl_date", data.get("date_crawled", "N/A"))
        body = data.get("content_markdown") or data.get("content") or ""

        content = (
            f"# {title}\n\n"
            f"**Source:** {source}\n\n"
            f"**URL:** {url}\n\n"
            f"**Crawled:** {crawl_date}\n\n"
            "---\n\n"
            f"{body.strip()}\n"
        )

        output_path = output_dir / f"{filepath.stem}.md"
        output_path.write_text(content, encoding="utf-8")
        print(f"  Saved: {output_path}")


def convert_all() -> None:
    """Run the full conversion pipeline."""
    print("=" * 50)
    print("Task 3: Convert landing files to Markdown")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print(f"\nDone. Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
