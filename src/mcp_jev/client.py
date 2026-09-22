"""HTTP client for the TypeSafe System One (Jev) API."""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any

import httpx

from mcp_jev.models import ValidationError, validate_questions

DEFAULT_API_BASE = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT_SEC = 30
DEFAULT_MAX_RETRIES = 3
RETRYABLE_STATUSES = frozenset({429, 529})
BACKOFF_SECONDS = (1.0, 2.0, 4.0)


class JevApiError(Exception):
    """Raised when the TypeSafe API returns an error response."""

    def __init__(
        self,
        status: int,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.details = details or {}


class JevClient:
    """Thin adapter around POST /v1/systemone."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str | None = None,
        timeout_sec: float | None = None,
        max_retries: int | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.environ.get("TYPESAFE_API_KEY", "")
        self.api_base = (api_base or os.environ.get("JEV_API_BASE") or DEFAULT_API_BASE).rstrip(
            "/"
        )
        self.default_model = (
            default_model or os.environ.get("JEV_DEFAULT_MODEL") or DEFAULT_MODEL
        )
        self.timeout_sec = float(
            timeout_sec if timeout_sec is not None else os.environ.get("JEV_TIMEOUT_SEC", DEFAULT_TIMEOUT_SEC)
        )
        self.max_retries = int(
            max_retries
            if max_retries is not None
            else os.environ.get("JEV_MAX_RETRIES", DEFAULT_MAX_RETRIES)
        )
        self._http_client = http_client

    def decide(
        self,
        state: str | dict[str, Any] | list[Any],
        questions: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise JevApiError(
                401,
                "Missing or invalid API key. Set TYPESAFE_API_KEY in the environment.",
            )

        validate_questions(questions)

        payload = {
            "model": model or self.default_model,
            "state": state,
            "questions": questions,
        }

        response = self._post_with_retries(payload)
        return {
            "model": response.get("model", payload["model"]),
            "answers": response.get("answers", {}),
            "usage": response.get("usage", {}),
        }

    def _post_with_retries(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.api_base}/v1/systemone"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        attempts = 0
        while True:
            attempts += 1
            response = self._request(url, headers, payload)

            if response.status_code == 200:
                return response.json()

            if response.status_code in RETRYABLE_STATUSES and attempts <= self.max_retries:
                delay = self._retry_delay(response, attempts)
                time.sleep(delay)
                continue

            raise self._error_from_response(response)

    def _request(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
    ) -> httpx.Response:
        if self._http_client is not None:
            return self._http_client.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout_sec,
            )

        with httpx.Client(timeout=self.timeout_sec) as client:
            return client.post(url, headers=headers, json=payload)

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass

        base = BACKOFF_SECONDS[min(attempt - 1, len(BACKOFF_SECONDS) - 1)]
        return base + random.uniform(0, 0.25)

    def _error_from_response(self, response: httpx.Response) -> JevApiError:
        status = response.status_code
        details: dict[str, Any] = {}

        try:
            body = response.json()
            if isinstance(body, dict):
                details = body
        except json.JSONDecodeError:
            body = None

        if status == 401:
            message = "Missing or invalid API key. Check TYPESAFE_API_KEY."
        elif status == 422:
            message = self._validation_message(details, response.text)
        else:
            snippet = response.text[:500] if response.text else "(empty response)"
            message = f"TypeSafe API error ({status}): {snippet}"

        return JevApiError(status, message, details)

    @staticmethod
    def _validation_message(details: dict[str, Any], fallback_text: str) -> str:
        for key in ("detail", "message", "error"):
            value = details.get(key)
            if isinstance(value, str) and value.strip():
                return f"Validation failed: {value}"
            if value is not None:
                return f"Validation failed: {value}"

        if fallback_text.strip():
            return f"Validation failed: {fallback_text[:500]}"

        return "Validation failed."


def format_validation_error(error: ValidationError) -> JevApiError:
    return JevApiError(422, error.message, error.details)
