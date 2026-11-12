"""Settings shared by the scripts: where the app is, which LLM, which Memgraph.

Values come from environment variables, or from a `.env` file in the repo root
(copy `.env.example`).
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

OUTPUT_DIR = REPO_ROOT / "output"
QUERIES_DIR = REPO_ROOT / "queries"
PROMPTS_DIR = REPO_ROOT / "prompts"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-5.5"}
LLM_MODEL = os.getenv("LLM_MODEL", "").strip() or DEFAULT_MODELS.get(LLM_PROVIDER, "")

MEMGRAPH_URI = os.getenv("MEMGRAPH_URI", "bolt://localhost:7687")


def app_dir(override: str | None = None) -> Path:
    """The movie-watchlist repo: --app, then APP_DIR, then ../movie-watchlist."""
    raw = override or os.getenv("APP_DIR") or str(REPO_ROOT.parent / "movie-watchlist")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    if not (path / "src").is_dir():
        sys.exit(
            f"Cannot find the movie-watchlist app at {path}.\n"
            "Clone it next to this repo (git clone https://github.com/tisserapac/movie-watchlist.git)\n"
            "or pass --app <path> (or set APP_DIR in .env)."
        )
    return path
