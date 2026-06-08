"""Task 1 - Legal document collection.

The required PDF files are placed in data/landing/legal. This script verifies
the folder and prints the collected files.
"""

from pathlib import Path

LEGAL_DIR = Path(__file__).resolve().parent.parent / "data" / "landing" / "legal"
VALID_EXTENSIONS = {".pdf", ".doc", ".docx"}


def setup_directory() -> Path:
    LEGAL_DIR.mkdir(parents=True, exist_ok=True)
    return LEGAL_DIR


def list_legal_documents() -> list[Path]:
    setup_directory()
    return sorted(
        path for path in LEGAL_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS
    )


def collection_summary() -> dict:
    files = list_legal_documents()
    return {
        "folder": str(LEGAL_DIR),
        "count": len(files),
        "files": [{"name": path.name, "bytes": path.stat().st_size} for path in files],
    }


if __name__ == "__main__":
    summary = collection_summary()
    print(f"Collected {summary['count']} legal documents in {summary['folder']}")
    for item in summary["files"]:
        print(f"- {item['name']} ({item['bytes']} bytes)")
