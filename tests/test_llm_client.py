from unittest.mock import MagicMock, patch

import pytest

from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import FactQuery


def _mock_settings():
    settings = MagicMock()
    settings.ark_api_key = "test-key"
    settings.ark_base_url = "https://test.example.com/api/v3"
    settings.ark_model = "test-model"
    return settings


def _make_completion(refusal=None, parsed=None, prompt_tokens=10, completion_tokens=5):
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.refusal = refusal
    completion.choices[0].message.parsed = parsed
    completion.usage = MagicMock()
    completion.usage.prompt_tokens = prompt_tokens
    completion.usage.completion_tokens = completion_tokens
    return completion


def test_llm_client_parses_response(monkeypatch):
    tracker = CostTracker()
    settings = _mock_settings()
    client = LLMClient(tracker, settings=settings)

    mock_completion = _make_completion(parsed=FactQuery(entity="Test", attributes=["a"]))
    monkeypatch.setattr(client.client.beta.chat.completions, "parse", lambda **kwargs: mock_completion)

    result = client.chat("system", "user", FactQuery)
    assert result.entity == "Test"
    assert tracker.llm_prompt_tokens == 10
    assert tracker.llm_completion_tokens == 5


def test_llm_client_refusal_raises_runtime_error(monkeypatch):
    tracker = CostTracker()
    settings = _mock_settings()
    client = LLMClient(tracker, settings=settings)

    mock_completion = _make_completion(refusal="I cannot answer this", parsed=None)
    monkeypatch.setattr(client.client.beta.chat.completions, "parse", lambda **kwargs: mock_completion)

    with pytest.raises(RuntimeError, match="Model refused"):
        client.chat("system", "user", FactQuery)


def test_llm_client_missing_choices_raises_runtime_error(monkeypatch):
    tracker = CostTracker()
    settings = _mock_settings()
    client = LLMClient(tracker, settings=settings)

    mock_completion = MagicMock()
    mock_completion.choices = []
    mock_completion.usage = MagicMock()
    monkeypatch.setattr(client.client.beta.chat.completions, "parse", lambda **kwargs: mock_completion)

    with pytest.raises(RuntimeError, match="no choices"):
        client.chat("system", "user", FactQuery)


def test_llm_client_missing_usage_raises_runtime_error(monkeypatch):
    tracker = CostTracker()
    settings = _mock_settings()
    client = LLMClient(tracker, settings=settings)

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.refusal = None
    mock_completion.choices[0].message.parsed = FactQuery(entity="Test", attributes=["a"])
    mock_completion.usage = None
    monkeypatch.setattr(client.client.beta.chat.completions, "parse", lambda **kwargs: mock_completion)

    with pytest.raises(RuntimeError, match="missing usage"):
        client.chat("system", "user", FactQuery)


def test_llm_client_retries_on_transient_error_then_succeeds(monkeypatch):
    tracker = CostTracker()
    settings = _mock_settings()
    client = LLMClient(tracker, settings=settings)

    mock_completion = _make_completion(parsed=FactQuery(entity="Retry", attributes=["b"]))
    call_count = 0

    def flaky_parse(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            from openai import APIConnectionError

            raise APIConnectionError(message="connection failed", request=MagicMock())
        return mock_completion

    monkeypatch.setattr(client.client.beta.chat.completions, "parse", flaky_parse)

    result = client.chat("system", "user", FactQuery)
    assert result.entity == "Retry"
    assert call_count == 2


def test_llm_client_import_without_env_vars_does_not_instantiate_settings():
    """Importing the module should not require environment variables."""
    with patch.dict("os.environ", {}, clear=True):
        from PPT_Generator import llm_client as llm_client_module

        assert llm_client_module is not None
