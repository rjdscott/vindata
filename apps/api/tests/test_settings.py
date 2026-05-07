"""Settings hydration from environment."""

from __future__ import annotations

import pytest

from vindata_api.settings import Settings, get_settings


def test_defaults_are_sensible() -> None:
    s = Settings(_env_file=None)
    assert s.port == 8000
    assert s.log_level in {"debug", "info", "warning", "error"}
    assert s.title == "VinData API"


def test_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VINDATA_API_PORT", "9999")
    monkeypatch.setenv("VINDATA_API_LOG_LEVEL", "debug")
    monkeypatch.setenv("VINDATA_API_CORS_ORIGINS", "https://a.example, https://b.example")
    s = Settings(_env_file=None)
    assert s.port == 9999
    assert s.log_level == "debug"
    assert s.cors_origins_list == ["https://a.example", "https://b.example"]


def test_log_level_pattern_rejects_garbage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VINDATA_API_LOG_LEVEL", "shouty")
    with pytest.raises(ValueError, match="pattern"):
        Settings(_env_file=None)


def test_get_settings_is_cached() -> None:
    a = get_settings()
    b = get_settings()
    assert a is b
