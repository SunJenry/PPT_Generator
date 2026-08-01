from unittest.mock import MagicMock

from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import FactQuery


def test_llm_client_parses_response(monkeypatch):
    tracker = CostTracker()
    client = LLMClient(tracker)

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.refusal = None
    mock_completion.choices[0].message.parsed = FactQuery(entity="Test", attributes=["a"])
    mock_completion.usage.prompt_tokens = 10
    mock_completion.usage.completion_tokens = 5

    monkeypatch.setattr(client.client.beta.chat.completions, "parse", lambda **kwargs: mock_completion)

    result = client.chat("system", "user", FactQuery)
    assert result.entity == "Test"
    assert tracker.llm_prompt_tokens == 10
