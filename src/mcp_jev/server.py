"""MCP server entry point for Jev."""

from __future__ import annotations

import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from mcp_jev.client import JevApiError, JevClient, format_validation_error
from mcp_jev.config import http_settings, transport_mode
from mcp_jev.env import load_repo_env
from mcp_jev.models import ValidationError

load_repo_env()

INSTRUCTIONS = (
    "Calls TypeSafe Jev for fast structured decisions (yes/no, choice, score). "
    "Use when you need calibrated probabilities, not generated prose."
)

mcp = MCPServer("jev", instructions=INSTRUCTIONS)
_client = JevClient()


def _json_response(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2)


@mcp.tool()
def jev_decide(
    state: str | dict[str, Any] | list[Any],
    questions: dict[str, Any],
    model: str | None = None,
) -> str:
    """Evaluate a state against typed Jev questions and return structured probabilities."""
    try:
        result = _client.decide(state=state, questions=questions, model=model)
        return _json_response(result)
    except ValidationError as exc:
        api_error = format_validation_error(exc)
        return _json_response(
            {
                "error": True,
                "status": api_error.status,
                "message": api_error.message,
                "details": api_error.details,
            }
        )
    except JevApiError as exc:
        return _json_response(
            {
                "error": True,
                "status": exc.status,
                "message": exc.message,
                "details": exc.details,
            }
        )
    except Exception as exc:  # noqa: BLE001 - surface unexpected failures as structured errors
        return _json_response(
            {
                "error": True,
                "status": 500,
                "message": f"Unexpected server error: {exc}",
                "details": {},
            }
        )


def main() -> None:
    mode = transport_mode()
    if mode == "streamable-http":
        mcp.run(transport="streamable-http", **http_settings())
        return

    if mode != "stdio":
        raise ValueError(f"Unsupported JEV_TRANSPORT: {mode!r}")

    mcp.run()


if __name__ == "__main__":
    main()
