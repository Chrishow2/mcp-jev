"""Unit tests for the MCP server tool handler."""

from __future__ import annotations

import json

import pytest

from mcp_jev import server
from mcp_jev.client import JevApiError, JevClient


SAMPLE_QUESTIONS = {
    "is_billing": {
        "type": "noul",
        "instructions": "Is message about billing?",
    }
}


class FakeClient:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.result = result or {
            "model": "jev-1.13.0",
            "answers": {"is_billing": {"type": "noul", "noul": 0.91}},
            "usage": {"input_tokens": 12, "output_tokens": 3},
        }
        self.error = error
        self.last_call = None

    def decide(self, state, questions, model=None):
        self.last_call = {"state": state, "questions": questions, "model": model}
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def restore_client():
    original = server._client
    yield
    server._client = original


def test_jev_decide_success_json_shape():
    server._client = FakeClient()

    raw = server.jev_decide(
        state={"message": "double charge"},
        questions=SAMPLE_QUESTIONS,
        model="jev-latest",
    )
    payload = json.loads(raw)

    assert "error" not in payload
    assert payload["model"] == "jev-1.13.0"
    assert payload["answers"]["is_billing"]["noul"] == 0.91


def test_jev_decide_api_error_json_shape():
    server._client = FakeClient(
        error=JevApiError(422, "Validation failed: bad criteria", {"field": "criteria"})
    )

    payload = json.loads(
        server.jev_decide(state={"message": "hello"}, questions=SAMPLE_QUESTIONS)
    )

    assert payload["error"] is True
    assert payload["status"] == 422
    assert payload["message"].startswith("Validation failed")


def test_jev_decide_tool_is_registered():
    tools = server.mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}

    assert "jev_decide" in names

    tool = next(item for item in tools if item.name == "jev_decide")
    assert "state" in tool.parameters["properties"]
    assert "questions" in tool.parameters["properties"]
    assert "state" in tool.parameters["required"]
    assert "questions" in tool.parameters["required"]
