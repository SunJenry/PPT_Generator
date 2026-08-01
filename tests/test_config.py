import os

import pytest

from PPT_Generator.config import Settings


def test_settings_reads_env_vars(monkeypatch):
    monkeypatch.setenv("ARK_API_KEY", "test-ark-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    s = Settings()
    assert s.ark_api_key == "test-ark-key"
    assert s.tavily_api_key == "test-tavily-key"
    assert s.ark_model == "kimi-k2.6"
