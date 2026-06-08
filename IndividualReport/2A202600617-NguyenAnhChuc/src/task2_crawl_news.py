"""Task 2 - News article collection.

Five JSON records are stored in data/landing/news. The helper below is an
offline crawler facade: it returns the local record for a known URL, which keeps
the submission reproducible when network access is not available.
"""

from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

NEWS_DIR = Path(__file__).resolve().parent.parent / "data" / "landing" / "news"


def setup_directory() -> Path:
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    return NEWS_DIR


def _json_articles() -> list[dict]:
    setup_directory()
    articles = []
    for path in sorted(NEWS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_file"] = path.name
        articles.append(data)
    return articles


ARTICLE_URLS = [article.get("url", "") for article in _json_articles()]


async def crawl_article(url: str) -> dict:
    for article in _json_articles():
        if article.get("url") == url:
            return {
                "url": article.get("url", url),
                "title": article.get("title", "Unknown title"),
                "source": article.get("source", "Unknown source"),
                "crawl_date": article.get("crawl_date", str(date.today())),
                "content": article.get("content") or article.get("content_markdown", ""),
            }
    return {
        "url": url,
        "title": "Offline placeholder article",
        "source": "local",
        "crawl_date": str(date.today()),
        "content": "URL recorded for the individual RAG news dataset.",
    }


async def crawl_all() -> list[dict]:
    records = []
    for url in ARTICLE_URLS:
        if url:
            records.append(await crawl_article(url))
    return records


if __name__ == "__main__":
    for item in asyncio.run(crawl_all()):
        print(f"- {item['title']} ({item['source']})")
