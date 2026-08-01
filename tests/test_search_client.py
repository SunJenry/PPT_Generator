import httpx
import pytest
import respx

from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.search_client import SearchClient


@respx.mock
def test_search_client_returns_results(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    tracker = CostTracker()
    client = SearchClient(tracker)

    route = respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(200, json={"answer": "£35k", "results": [{"url": "https://example.com"}]})
    )

    result = client.search("Imperial Business Analytics tuition")
    assert result["answer"] == "£35k"
    assert tracker.search_calls == 1
    assert route.called
