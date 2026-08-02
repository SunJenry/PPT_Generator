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


def _make_completion(refusal=None, content=None, prompt_tokens=10, completion_tokens=5):
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.refusal = refusal
    completion.choices[0].message.content = content
    completion.usage = MagicMock()
    completion.usage.prompt_tokens = prompt_tokens
    completion.usage.completion_tokens = completion_tokens
    return completion


def _make_client(mock_openai_class):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    tracker = CostTracker()
    client = LLMClient(tracker, settings=_mock_settings())
    return client, mock_client


def test_llm_client_parses_plain_json():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.chat.completions.create.return_value = _make_completion(
            content='{"entity": "Test", "attributes": ["a"]}'
        )

        result = client.chat("system", "user", FactQuery)
        assert result.entity == "Test"
        assert result.attributes == ["a"]


def test_llm_client_parses_json_with_markdown_fence():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.chat.completions.create.return_value = _make_completion(
            content='```json\n{"entity": "Test", "attributes": ["a"]}\n```'
        )

        result = client.chat("system", "user", FactQuery)
        assert result.entity == "Test"


def test_llm_client_records_usage():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.chat.completions.create.return_value = _make_completion(
            content='{"entity": "Test", "attributes": ["a"]}', prompt_tokens=10, completion_tokens=5
        )

        client.chat("system", "user", FactQuery)
        assert client.cost_tracker.llm_prompt_tokens == 10
        assert client.cost_tracker.llm_completion_tokens == 5


def test_llm_client_refusal_raises_runtime_error():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.chat.completions.create.return_value = _make_completion(refusal="I cannot answer this")

        with pytest.raises(RuntimeError, match="Model refused"):
            client.chat("system", "user", FactQuery)


def test_llm_client_missing_choices_raises_runtime_error():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_completion = MagicMock()
        mock_completion.choices = []
        mock_completion.usage = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        with pytest.raises(RuntimeError, match="no choices"):
            client.chat("system", "user", FactQuery)


def test_llm_client_invalid_json_raises_runtime_error():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.chat.completions.create.return_value = _make_completion(content="not json at all")

        with pytest.raises(RuntimeError, match="did not produce valid structured output"):
            client.chat("system", "user", FactQuery)


def test_llm_client_missing_usage_raises_runtime_error():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.refusal = None
        mock_completion.choices[0].message.content = '{"entity": "Test", "attributes": ["a"]}'
        mock_completion.usage = None
        mock_client.chat.completions.create.return_value = mock_completion

        with pytest.raises(RuntimeError, match="missing usage"):
            client.chat("system", "user", FactQuery)


def test_llm_client_retries_on_transient_error_then_succeeds():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        call_count = 0

        def flaky_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                from openai import APIConnectionError

                raise APIConnectionError(message="connection failed", request=MagicMock())
            return _make_completion(content='{"entity": "Retry", "attributes": ["b"]}')

        mock_client.chat.completions.create.side_effect = flaky_create

        result = client.chat("system", "user", FactQuery)
        assert result.entity == "Retry"
        assert call_count == 2


def test_llm_client_import_without_env_vars_does_not_instantiate_settings():
    """Importing the module should not require environment variables."""
    with patch.dict("os.environ", {}, clear=True):
        from PPT_Generator import llm_client as llm_client_module

        assert llm_client_module is not None
