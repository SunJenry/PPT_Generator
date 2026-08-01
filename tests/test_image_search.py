import httpx
import respx

from PPT_Generator import config
from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.image_search import ImageSearchClient


@respx.mock
def test_image_search_returns_url(monkeypatch):
    monkeypatch.setattr(config.settings, "unsplash_access_key", "test-key")
    tracker = CostTracker()
    client = ImageSearchClient(tracker)

    route = respx.get("https://api.unsplash.com/search/photos").mock(
        return_value=httpx.Response(200, json={"results": [{"urls": {"regular": "https://image.jpg"}}]})
    )

    url = client.search("university campus")
    assert url == "https://image.jpg"
    assert tracker.image_calls == 1
