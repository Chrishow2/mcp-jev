"""Load repo-local environment variables for local development."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]


def load_repo_env() -> Path | None:
    """Load `.env` from the repo root if present. Does not override existing env vars."""
    dotenv_path = _REPO_ROOT / ".env"
    if dotenv_path.is_file():
        load_dotenv(dotenv_path)
        return dotenv_path
    return None
