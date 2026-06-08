"""Configuration for the group RAG demo."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GROUP_ROOT = Path(__file__).resolve().parents[1]
STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"
SAMPLE_CORPUS_PATH = GROUP_ROOT / "data" / "sample_corpus.json"

load_dotenv(PROJECT_ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

DEFAULT_TOP_K = int(os.getenv("GROUP_RAG_TOP_K", "3"))
CHUNK_SIZE = int(os.getenv("GROUP_RAG_CHUNK_SIZE", "520"))
CHUNK_OVERLAP = int(os.getenv("GROUP_RAG_CHUNK_OVERLAP", "80"))
MIN_SCORE_FOR_ANSWER = float(os.getenv("GROUP_RAG_MIN_SCORE", "0.08"))
