"""Tests for runtime transport configuration."""

from mcp_jev.config import http_settings, transport_mode


def test_transport_defaults(monkeypatch):
    monkeypatch.delenv("JEV_TRANSPORT", raising=False)
    assert transport_mode() == "stdio"


def test_http_settings_from_env(monkeypatch):
    monkeypatch.setenv("JEV_HOST", "0.0.0.0")
    monkeypatch.setenv("JEV_PORT", "9000")
    monkeypatch.setenv("JEV_HTTP_PATH", "/api/mcp")
    monkeypatch.setenv("JEV_STATELESS_HTTP", "false")

    settings = http_settings()

    assert settings["host"] == "0.0.0.0"
    assert settings["port"] == 9000
    assert settings["streamable_http_path"] == "/api/mcp"
    assert settings["stateless_http"] is False
