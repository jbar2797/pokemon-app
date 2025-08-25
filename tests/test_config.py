from __future__ import annotations

import pytest

from poke_pricer.config import Settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.log_level in {"INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"}
    assert str(s.data_dir) == "data"


def test_settings_env_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POKEPRICER_LOG_LEVEL", "DEBUG")
    s = Settings()
    assert s.log_level == "DEBUG"
