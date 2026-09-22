"""Runtime configuration from environment variables."""

from __future__ import annotations

import os

DEFAULT_TRANSPORT = "stdio"
DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 8000
DEFAULT_HTTP_PATH = "/mcp"


def transport_mode() -> str:
    return os.environ.get("JEV_TRANSPORT", DEFAULT_TRANSPORT)


def http_settings() -> dict[str, object]:
    return {
        "host": os.environ.get("JEV_HOST", DEFAULT_HTTP_HOST),
        "port": int(os.environ.get("JEV_PORT", str(DEFAULT_HTTP_PORT))),
        "streamable_http_path": os.environ.get("JEV_HTTP_PATH", DEFAULT_HTTP_PATH),
        "stateless_http": os.environ.get("JEV_STATELESS_HTTP", "true").lower()
        in ("1", "true", "yes"),
    }
