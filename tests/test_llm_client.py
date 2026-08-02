from unittest.mock import MagicMock, patch

import pytest

from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline


def _mock_settings():
    settings = MagicMock()
    settings.deepseek_api_key = "test-key"
    settings.deepseek_base_url = "https://test.example.com"
    settings.deepseek_model = "deepseek-v4-flash"
    return settings


def _make_completion(output_text=None, input_tokens=10, output_tokens=5):
    completion = MagicMock()
    completion.output_text = output_text
    completion.usage = MagicMock()
    completion.usage.input_tokens = input_tokens
    completion.usage.output_tokens = output_tokens
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
        mock_client.responses.create.return_value = _make_completion(
            output_text='{"narrative_arc": "arc", "sections": [{"section_title": "Intro", "pages": 1, "key_points": ["a"]}]}'
        )

        result = client.chat("system", "user", Outline)
        assert result.narrative_arc == "arc"
        assert result.sections[0].section_title == "Intro"


def test_llm_client_parses_json_with_markdown_fence():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.responses.create.return_value = _make_completion(
            output_text='```json\n{"narrative_arc": "arc", "sections": [{"section_title": "Intro", "pages": 1, "key_points": ["a"]}]}\n```'
        )

        result = client.chat("system", "user", Outline)
        assert result.narrative_arc == "arc"


def test_llm_client_passes_web_search_tool_when_requested():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.responses.create.return_value = _make_completion(
            output_text='{"narrative_arc": "arc", "sections": [{"section_title": "Intro", "pages": 1, "key_points": ["a"]}]}'
        )

        client.chat("system", "user", Outline, use_search=True)
        call_kwargs = mock_client.responses.create.call_args.kwargs
        assert call_kwargs["tools"] == [{"type": "web_search"}]


def test_llm_client_omits_web_search_tool_by_default():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.responses.create.return_value = _make_completion(
            output_text='{"narrative_arc": "arc", "sections": [{"section_title": "Intro", "pages": 1, "key_points": ["a"]}]}'
        )

        client.chat("system", "user", Outline)
        call_kwargs = mock_client.responses.create.call_args.kwargs
        assert "tools" not in call_kwargs


def test_llm_client_records_usage():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.responses.create.return_value = _make_completion(
            output_text='{"narrative_arc": "arc", "sections": [{"section_title": "Intro", "pages": 1, "key_points": ["a"]}]}', input_tokens=10, output_tokens=5
        )

        client.chat("system", "user", Outline)
        assert client.cost_tracker.llm_prompt_tokens == 10
        assert client.cost_tracker.llm_completion_tokens == 5


def test_llm_client_invalid_json_raises_runtime_error():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.responses.create.return_value = _make_completion(output_text="not json at all")

        with pytest.raises(RuntimeError, match="did not produce valid structured output"):
            client.chat("system", "user", Outline)


def test_llm_client_empty_output_raises_runtime_error():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_client.responses.create.return_value = _make_completion(output_text="")

        with pytest.raises(RuntimeError, match="did not produce valid structured output"):
            client.chat("system", "user", Outline)


def test_llm_client_missing_usage_raises_runtime_error():
    with patch("PPT_Generator.llm_client.OpenAI") as mock_openai_class:
        client, mock_client = _make_client(mock_openai_class)
        mock_completion = MagicMock()
        mock_completion.output_text = '{"narrative_arc": "arc", "sections": [{"section_title": "Intro", "pages": 1, "key_points": ["a"]}]}'
        mock_completion.usage = None
        mock_client.responses.create.return_value = mock_completion

        with pytest.raises(RuntimeError, match="missing usage"):
            client.chat("system", "user", Outline)


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
            return _make_completion(output_text='{"narrative_arc": "retry", "sections": [{"section_title": "Intro", "pages": 1, "key_points": ["a"]}]}')

        mock_client.responses.create.side_effect = flaky_create

        result = client.chat("system", "user", Outline)
        assert result.narrative_arc == "retry"
        assert call_count == 2


def test_llm_client_import_without_env_vars_does_not_instantiate_settings():
    """Importing the module should not require environment variables."""
    with patch.dict("os.environ", {}, clear=True):
        from PPT_Generator import llm_client as llm_client_module

        assert llm_client_module is not None
