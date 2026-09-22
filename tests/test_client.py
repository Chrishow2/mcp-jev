"""Unit tests for the TypeSafe Jev HTTP client."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from mcp_jev.client import JevApiError, JevClient
from mcp_jev.models import ValidationError

FIXTURES = Path(__file__).parent / "fixtures"


def _success_payload() -> dict:
    return json.loads((FIXTURES / "systemone_success.json").read_text(encoding="utf-8"))


def _mock_transport(responses: list[httpx.Response]) -> httpx.MockTransport:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        index = min(calls["count"], len(responses) - 1)
        calls["count"] += 1
        return responses[index]

    return httpx.MockTransport(handler)


def _client_with_responses(responses: list[httpx.Response], **kwargs) -> JevClient:
    http_client = httpx.Client(transport=_mock_transport(responses))
    return JevClient(
        api_key="sk-test",
        api_base="https://api.typesafe.ai",
        max_retries=3,
        http_client=http_client,
        **kwargs,
    )


SAMPLE_QUESTIONS = {
    "is_billing": {
        "type": "noul",
        "instructions": "Is message about billing?",
    }
}


def test_decide_happy_path():
    payload = _success_payload()
    client = _client_with_responses([httpx.Response(200, json=payload)])

    result = client.decide(
        state={"message": "My card was charged twice."},
        questions=SAMPLE_QUESTIONS,
    )

    assert result["model"] == "jev-1.13.0"
    assert result["answers"]["is_sponsor_inquiry"]["noul"] == 0.99
    assert result["usage"]["input_tokens"] == 210


def test_decide_missing_api_key():
    client = JevClient(api_key="")

    with pytest.raises(JevApiError) as exc:
        client.decide(state={"message": "hello"}, questions=SAMPLE_QUESTIONS)

    assert exc.value.status == 401


def test_decide_401_from_api():
    client = _client_with_responses([httpx.Response(401, json={"detail": "Unauthorized"})])

    with pytest.raises(JevApiError) as exc:
        client.decide(state={"message": "hello"}, questions=SAMPLE_QUESTIONS)

    assert exc.value.status == 401
    assert "API key" in exc.value.message


def test_decide_422_from_api():
    client = _client_with_responses(
        [httpx.Response(422, json={"detail": "Invalid questions payload"})]
    )

    with pytest.raises(JevApiError) as exc:
        client.decide(state={"message": "hello"}, questions=SAMPLE_QUESTIONS)

    assert exc.value.status == 422
    assert "Validation failed" in exc.value.message


def test_decide_retries_on_529_then_succeeds(monkeypatch):
    payload = _success_payload()
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] < 3:
            return httpx.Response(529, json={"detail": "overloaded"})
        return httpx.Response(200, json=payload)

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = JevClient(
        api_key="sk-test",
        api_base="https://api.typesafe.ai",
        max_retries=3,
        http_client=http_client,
    )
    monkeypatch.setattr("mcp_jev.client.time.sleep", lambda _: None)

    result = client.decide(state={"message": "hello"}, questions=SAMPLE_QUESTIONS)

    assert call_count["n"] == 3
    assert result["answers"]["is_sponsor_inquiry"]["type"] == "noul"


def test_validate_questions_before_request():
    client = _client_with_responses([httpx.Response(500, json={"detail": "should not hit"})])

    with pytest.raises(ValidationError):
        client.decide(
            state={"message": "hello"},
            questions={"bad": {"type": "noul", "instructions": ""}},
        )


def test_other_status_includes_snippet():
    client = _client_with_responses([httpx.Response(500, text="internal failure")])

    with pytest.raises(JevApiError) as exc:
        client.decide(state={"message": "hello"}, questions=SAMPLE_QUESTIONS)

    assert exc.value.status == 500
    assert "internal failure" in exc.value.message
